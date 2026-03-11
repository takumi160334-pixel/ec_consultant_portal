import os
import json
import time
from google import genai
from google.genai import types

# Load API key directly from the env of the workspace if possible, or fallback
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'ec_news_reader', '.env'))
except ImportError:
    pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is missing.")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = 'gemini-2.5-flash'

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'data')
EC_NEWS_READER_DATA = os.path.join(os.path.dirname(__file__), '..', '..', 'ec_news_reader', 'processed_news.json')

ALLOWED_THEMES = ["EC業界知識", "EC運営基礎知識", "楽天市場", "ヤフーショッピング", "Amazon", "Qoo10", "TikTokshop"]

def load_json_safe(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def validate_schema_and_theme(parsed_json):
    """Auto-healing validation logic. Raises ValueError if validation fails."""
    if not isinstance(parsed_json, dict):
        raise ValueError("Root element must be a dictionary.")
    
    for key, item in parsed_json.items():
        if key in ["manual", "quiz", "case_study"]:
            if "theme" not in item:
                raise ValueError(f"Missing 'theme' key in {key}.")
            if item["theme"] not in ALLOWED_THEMES:
                raise ValueError(f"Invalid theme '{item['theme']}' in {key}. Must be one of: {', '.join(ALLOWED_THEMES)}.")
            if "original_source" not in item:
                raise ValueError(f"Missing 'original_source' key in {key}.")
            
        if key == "quiz":
            if "options" not in item or not isinstance(item["options"], list) or len(item["options"]) != 4:
                raise ValueError("Quiz must have exactly 4 options.")
            if "correct_answer" not in item or not isinstance(item["correct_answer"], int):
                raise ValueError("Quiz must have a 'correct_answer' integer index.")
        
        if key == "case_study":
            if "evaluation_rubric" not in item or not isinstance(item["evaluation_rubric"], list) or len(item["evaluation_rubric"]) == 0:
                raise ValueError("Case study must have an 'evaluation_rubric' list with at least one item.")


def process_raw_data():
    """Reads raw data, uses LLM to categorize into Manuals, Quizzes, Cases, News and saves."""
    raw_yt = load_json_safe(os.path.join(DATA_DIR, 'raw_youtube.json'))
    raw_rss = load_json_safe(os.path.join(DATA_DIR, 'raw_rss.json'))
    
    # Load previously existing data to append
    manuals = load_json_safe(os.path.join(DATA_DIR, 'manuals.json'))
    quizzes = load_json_safe(os.path.join(DATA_DIR, 'quizzes.json'))
    cases = load_json_safe(os.path.join(DATA_DIR, 'cases.json'))
    news = load_json_safe(os.path.join(DATA_DIR, 'news.json'))

    # Helper function to check if ID exists
    def exists(item_id, collection):
        return any(item.get('id') == item_id for item in collection)

    items_to_process = raw_yt[:5] + raw_rss[:10] # Increased daily volume significantly (15 total)

    print(f"Processing {len(items_to_process)} raw items with Gemini in a single batch...")

    if not items_to_process:
        print("No items to process.")
        return

    input_payload = ""
    for i, item in enumerate(items_to_process):
        source_type = item.get('type', 'unknown')
        title = item.get('title', '')
        text = item.get('text', '')[:1000] # Truncate to save tokens for batching
        source_url = item.get('source_url', '')
        source_name = item.get('source_name', 'YouTube')
        input_payload += f"--- ARTICLE INDEX: {i} ---\nTYPE: {source_type} ({source_name})\nTITLE: {title}\nURL: {source_url}\nTEXT: {text}\n\n"

    base_prompt = f"""
あなたはプロのECコンサルタント育成用コンテンツクリエイターです。
以下の複数の情報（当日のニュースやトレンド）をもとに、初心者コンサルタント向けの教育コンテンツを一括で作成してください。

【最重要：動的ケーススタディとクイズの絶対生成】
単にニュースを要約するだけでなく、そのニュースが「EC売上の方程式（アクセス数 × CVR × 客単価）」などの重要KPIにどう影響するかを分析し、**必ず1つ以上のケーススタディ(case_study)と、1つ以上のクイズ(quiz)を新規生成してください。**
これにより、毎日のニュースが「常に更新され続ける実戦問題集」となります。

以下のJSON配列形式で出力してください。Markdownコードブロック(```json)は含めず、純粋なJSON配列のみを出力してください。

【重要：テーマ分類】
manual, quiz, case_study を生成する場合、必ず以下のテーマのいずれか1つを正確に `theme` キーに設定してください。
許容されるテーマ: "EC業界知識", "EC運営基礎知識", "楽天市場", "ヤフーショッピング", "Amazon", "Qoo10", "TikTokshop"

【出力形式の例】
[
  {{
      "index": 0,
      "news": {{
          "title": "（ニュースの要約タイトル）",
          "summary": "（コンサル視点でのニュースの意義を2-3行で）",
          "original_source": "https://..."
      }},
      "manual": {{
          "title": "（内容に基づくマニュアルのタイトル）",
          "theme": "（許容されるテーマから1つ選択）",
          "category": "基礎知識/トレンド",
          "content": "（Markdown形式での運用知識やヒントまとめ）",
          "original_source": "https://...",
          "tags": ["タグ1", "タグ2"]
      }},
      "quiz": {{
          "theme": "（許容されるテーマから1つ選択）",
          "question": "（情報に基づく4択問題）",
          "options": ["選択肢1", "選択肢2", "選択肢3", "選択肢4"],
          "correct_answer": 0,
          "explanation": "（なぜそれが正解なのかの解説）",
          "original_source": "https://..."
      }},
      "case_study": {{
          "title": "（テーマを用いたケーススタディのタイトル）",
          "theme": "（許容されるテーマから1つ選択）",
          "scenario": "（クライアント課題シナリオ）",
          "question": "（論理的思考を問う設問）",
          "evaluation_rubric": ["評価基準1", "評価基準2"],
          "example_solution": "（模範回答例）",
          "original_source": "https://..."
      }}
  }},
  {{
      "index": 1,
      "news": {{
          "title": "...",
          "summary": "...",
          "original_source": "..."
      }}
  }}
]

【記事データ】
{input_payload}
"""

    max_retries = 3
    base_delay = 5
    current_prompt = base_prompt

    for attempt in range(max_retries):
        try:
            print(f"  -> Calling Gemini for batch (Attempt {attempt + 1})")
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=current_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                )
            )
            
            resp_text = response.text.strip()
            if resp_text.startswith('```json'): resp_text = resp_text[7:]
            if resp_text.startswith('```'): resp_text = resp_text[3:]
            if resp_text.endswith('```'): resp_text = resp_text[:-3]

            parsed_array = json.loads(resp_text.strip())
            
            if not isinstance(parsed_array, list):
                raise ValueError("Root element must be a JSON array (list).")
            
            # Auto-healing validation
            # Track any errors to raise them and retry the batch if completely corrupted
            validation_errors = []
            for parsed in parsed_array:
                if not isinstance(parsed, dict) or "index" not in parsed:
                    continue
                try:
                    validate_schema_and_theme(parsed)
                except ValueError as ve:
                    validation_errors.append(f"Index {parsed.get('index')}: {ve}")
            
            if len(validation_errors) == len(parsed_array) and len(parsed_array) > 0:
                raise ValueError("\\n".join(validation_errors))
            
            cur_date = time.strftime("%Y-%m-%d")
            
            for parsed in parsed_array:
                if not isinstance(parsed, dict): continue
                idx = parsed.get("index")
                if idx is None or idx < 0 or idx >= len(items_to_process):
                    continue
                
                orig_item = items_to_process[idx]
                source_type = orig_item.get('type', 'unknown')
                base_id = f"{source_type}-{time.time()}-{idx}"
                
                if "manual" in parsed and "title" in parsed["manual"]:
                    parsed["manual"]["id"] = f"man-{base_id}"
                    parsed["manual"]["last_updated"] = cur_date
                    manuals.append(parsed["manual"])
                
                if "quiz" in parsed and "question" in parsed["quiz"]:
                    parsed["quiz"]["id"] = f"quiz-{base_id}"
                    quizzes.append(parsed["quiz"])
                    
                if "case_study" in parsed and "scenario" in parsed["case_study"]:
                    parsed["case_study"]["id"] = f"case-{base_id}"
                    cases.append(parsed["case_study"])

                if "news" in parsed and "summary" in parsed["news"]:
                    parsed["news"]["id"] = f"news-{base_id}"
                    parsed["news"]["date"] = cur_date
                    news.append(parsed["news"])
            
            break # Success
            
        except json.JSONDecodeError as e:
            print(f"    [Auto-Healing] JSON Decode Error: {e}")
            current_prompt = base_prompt + f"\n\n前回の出力でJSONの構文エラーが発生しました。純粋なJSON配列のみを出力してください。エラー詳細: {e}"
            time.sleep(2)
        except ValueError as e:
            print(f"    [Auto-Healing] Schema/Theme/Format Validation Error: {e}")
            current_prompt = base_prompt + f"\n\n前回の出力で全アイテムに検証エラーが発生しました。指示された配列フォーマット、オブジェクト構造、許容されるテーマを厳密に守ってください。各オブジェクトには `index` を含めてください。エラー詳細: {e}"
            time.sleep(2)
        except Exception as e:
            error_msg = str(e)
            print(f"Error calling API (Attempt {attempt + 1}): {error_msg}")
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                sleep_time = base_delay * (attempt + 1) * 2
                print(f"    Rate limited. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                time.sleep(5)

    # Bring in ec_news_reader output if available
    ec_news = load_json_safe(EC_NEWS_READER_DATA)
    if ec_news:
        print(f"Merging {len(ec_news)} items from existing ec_news_reader...")
        for enews in ec_news:
            # check if title already in news array to avoid extreme duplication
            if not any(n.get("title") == enews.get("title") for n in news):
                news.append({
                    "id": f"ecnews-{time.time()}",
                    "title": enews.get("title", "EC News Update"),
                    "summary": enews.get("tips", enews.get("summary", "")),
                    "original_source": enews.get("source", "ec_news_reader system"),
                    "date": time.strftime("%Y-%m-%d")
                })

    # Save outputs
    with open(os.path.join(DATA_DIR, 'manuals.json'), 'w', encoding='utf-8') as f:
        json.dump(manuals, f, ensure_ascii=False, indent=4)
    with open(os.path.join(DATA_DIR, 'quizzes.json'), 'w', encoding='utf-8') as f:
        json.dump(quizzes, f, ensure_ascii=False, indent=4)
    with open(os.path.join(DATA_DIR, 'cases.json'), 'w', encoding='utf-8') as f:
        json.dump(cases, f, ensure_ascii=False, indent=4)
    with open(os.path.join(DATA_DIR, 'news.json'), 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=4)

    print("Data processing complete. Saved manuals, quizzes, cases, and news.")

if __name__ == "__main__":
    process_raw_data()

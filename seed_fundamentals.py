import os
import json
import time
from google import genai
from google.genai import types

# Load API key
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'ec_news_reader', '.env'))
except ImportError:
    pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = 'gemini-2.5-flash' # Use flash to avoid rate limits

DATA_DIR = os.path.join(os.path.dirname(__file__), 'frontend', 'data')

def generate_fundamentals():
    print("Generating comprehensive foundational knowledge...")
    
    themes = [
        "EC運営基礎知識",
        "楽天市場",
        "ヤフーショッピング",
        "Amazon",
        "Qoo10",
        "TikTokshop"
    ]
    
    sub_themes = [
        "販促イベントと広告運用（アクセス数最大化）",
        "CRMと各種施策（CVR・客単価・LTV最大化）"
    ]
    
    all_parsed = []
    
    for theme in themes:
        for sub in sub_themes:
            print(f"  -> Generating [ {theme} ] x [ {sub} ]...")
            prompt = f"""
あなたは、EC未経験者をプロのコンサルタントに育成する最高峰の教育AIです。
「{theme}」における「{sub}」に特化した、深く実践的で網羅的な基礎知識を作成してください。

【必須条件】
- 必ず「EC売上の方程式（アクセス×CVR×客単価）」、またはCPA/ROAS等の概念と紐付けて解説・出題してください。
- manual（マニュアル）、quiz（クイズ）、case_study（ケーススタディ）をそれぞれ最低2〜3個ずつ、合計6〜9個生成してください。
- manualの `content` と case_studyの `example_solution` は、見出しや箇条書きを用いたリッチなMarkdown形式で、文字数を惜しまず詳細に解説してください。
- クイズ(quiz)は必ず4つの選択肢(options)を含め、正解(correct_answer)は0〜3の整数にしてください。
- themeの値は必ず "{theme}" と完全一致させてください（表記ブレNG）。
- 出力は純粋なJSON配列のみ。Markdownコードブロックは不要です。

【JSON構造の例】
[
    {{
        "manual": {{ "title": "...", "theme": "{theme}", "category": "基礎", "content": "Markdown...", "original_source": "自社作成", "tags": ["..."] }}
    }},
    {{
        "quiz": {{ "theme": "{theme}", "question": "...", "options": ["A","B","C","D"], "correct_answer": 0, "explanation": "...", "original_source": "自社作成" }}
    }}
]
"""

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Give it a tiny sleep to relieve API burst pressure
                    time.sleep(1)
                    response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.3,
                            response_mime_type="application/json",
                        )
                    )
                    
                    resp_text = response.text.strip()
                    if resp_text.startswith('```json'): resp_text = resp_text[7:]
                    if resp_text.startswith('```'): resp_text = resp_text[3:]
                    if resp_text.endswith('```'): resp_text = resp_text[:-3]

                    parsed_array = json.loads(resp_text.strip())
                    all_parsed.extend(parsed_array)
                    print(f"     Successfully generated {len(parsed_array)} items.")
                    break
                except Exception as e:
                    print(f"     Error on attempt {attempt+1} for {theme}-{sub}: {e}")
                    time.sleep(8)
    
    
    # Process all_parsed
    manuals = []
    quizzes = []
    cases = []
    
    for parsed in all_parsed:
        if not isinstance(parsed, dict): continue
        base_id = f"fundamental-{time.time()}-{id(parsed)}"
        
        if "manual" in parsed and "title" in parsed["manual"]:
            parsed["manual"]["id"] = f"man-{base_id}"
            parsed["manual"]["last_updated"] = time.strftime("%Y-%m-%d")
            manuals.append(parsed["manual"])
        
        if "quiz" in parsed and "question" in parsed["quiz"]:
            parsed["quiz"]["id"] = f"quiz-{base_id}"
            quizzes.append(parsed["quiz"])
            
        if "case_study" in parsed and "scenario" in parsed["case_study"]:
            parsed["case_study"]["id"] = f"case-{base_id}"
            cases.append(parsed["case_study"])

    # Load existing
    try:
        with open(os.path.join(DATA_DIR, 'manuals.json'), 'r', encoding='utf-8') as f:
            existing_manuals = json.load(f)
    except: existing_manuals = []
    try:
        with open(os.path.join(DATA_DIR, 'quizzes.json'), 'r', encoding='utf-8') as f:
            existing_quizzes = json.load(f)
    except: existing_quizzes = []
    try:
        with open(os.path.join(DATA_DIR, 'cases.json'), 'r', encoding='utf-8') as f:
            existing_cases = json.load(f)
    except: existing_cases = []

    # Prepend new to existing
    manuals.extend(existing_manuals)
    quizzes.extend(existing_quizzes)
    cases.extend(existing_cases)

    with open(os.path.join(DATA_DIR, 'manuals.json'), 'w', encoding='utf-8') as f:
        json.dump(manuals, f, ensure_ascii=False, indent=4)
    with open(os.path.join(DATA_DIR, 'quizzes.json'), 'w', encoding='utf-8') as f:
        json.dump(quizzes, f, ensure_ascii=False, indent=4)
    with open(os.path.join(DATA_DIR, 'cases.json'), 'w', encoding='utf-8') as f:
        json.dump(cases, f, ensure_ascii=False, indent=4)
        
    print(f"Generated a total of {len(all_parsed)} foundational items!")

if __name__ == "__main__":
    generate_fundamentals()

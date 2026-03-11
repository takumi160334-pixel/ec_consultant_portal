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
    
    all_parsed = []
    
    for theme in themes:
        print(f"  -> Generating for theme: {theme}...")
        prompt = f"""
あなたは、EC未経験者や初心者をプロのECコンサルタントに育成するための、最高峰の教育コンテンツクリエイターです。
ユーザーからは、「最新ニュースではなく、EC運営における公式（売上=訪問数×CVR×客単価、CPA、ROAS等）や、各モールの基礎知識、ルール、専門用語を優先したマニュアル・クイズ・ケーススタディを【網羅的に大量に】作成してほしい」と強い要望を受けています。

今回は以下のテーマに絞って、非常に詳しく、実践的で、初心者が基礎から体系的に学べる**マニュアル（manual）**、**クイズ（quiz）**、**ケーススタディ（case_study）**を作成し、JSON配列として出力してください。

【対象テーマ】
"{theme}"

【必須網羅項目】
「EC売上の方程式（アクセス×CVR×客単価）」を軸に、以下の手法をすべて掛け合わせて具体的に解説してください。
- 販促イベント（楽天スーパーSALE、お買い物マラソン、Qoo10メガ割、Amazonプライムデーなど）
- 各種広告（楽天RPP、Amazonスポンサープロダクト、Yahoo!プロモーションパッケージなど）
- クリエイティブ/商品ページ改善（A+コンテンツ、白背景画像、サムネイルABテスト、SEOキーワード最適化など）
- CRM（LINE配信、メルマガ、同梱物、リピート施策）
- フルフィルメント/物流（Amazon FBA、Yahoo!優良配送、楽天スーパーロジスティクス等）

【ケーススタディの『更新性と汎用性』】
case_studyのシナリオは、「もしROASがXXX%で、CVRがYY%に落ちた場合で、〇〇というイベントが控えている」のように、様々な変数のパターンを掛け合わせた実践的な問題を作成してください。読者があらゆるパターンを想定して思考訓練できるような作りにしてください。

【生成ルール】
- manual, quiz, case_studyをそれぞれ最低3〜4個生成してください。
- manualの `content` は、単語帳サイズではなく、Markdown形式（見出し `###`、太字 `**`、箇条書き `-` など）をフル活用した深い解説本文にしてください。
- case_studyの `example_solution` も同様にMarkdownをフル活用して模範解答を論理的に書いてください。
- すべての出力において `theme` は必ず "{theme}" と完全に一致させてください。
- 出力は純粋なJSON配列のみとしてください。Markdownコードブロック(```json)は含めないでください。

【JSON構造の例】
[
    {{
        "manual": {{
            "title": "...",
            "theme": "{theme}",
            "category": "...",
            "content": "...",
            "original_source": "自社オリジナル作成知識",
            "tags": ["..."]
        }}
    }}
]
"""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt,
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
                all_parsed.extend(parsed_array)
                print(f"     Successfully generated {len(parsed_array)} items for {theme}.")
                break
            except Exception as e:
                print(f"     Error on attempt {attempt+1}: {e}")
                time.sleep(5)
    
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

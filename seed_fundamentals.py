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
    
    prompt = """
あなたは、EC未経験者や初心者をプロのECコンサルタントに育成するための、最高峰の教育コンテンツクリエイターです。
ユーザーからは、「最新ニュースではなく、EC運営における公式（売上=顧客数×客単価、CPA、CVR、ROAS等）や、各モールの基礎知識、ルール、専門用語（楽天市場のRPP広告、ヤフーショッピング、Amazon等）を優先したマニュアル・クイズ・ケーススタディを作成してほしい」と強い要望を受けています。

以下の「テーマ」ごとに、非常に詳しく、実践的で、初心者が基礎から体系的に学べる**マニュアル（manual）**、**クイズ（quiz）**、**ケーススタディ（case_study）**をそれぞれ複数作成し、巨大なJSON配列として出力してください。
ニュース(news)は不要です。

【必須テーマ】
1. "EC運営基礎知識" (売上の公式: 訪問数×CVR×客単価、CPA、ROAS、LTVなどの重要指標の解説、ECサイト運営の基本業務)
2. "楽天市場" (RPP広告、スーパーSALE/お買い物マラソン、ポイント変倍、その他独自ルールや専門用語)
3. "ヤフーショッピング" (プロモーションパッケージ、優良配送、PayPayステップ等の独自ルール)
4. "Amazon" (FBA、スポンサープロダクト広告、ショッピングカートボックス獲得の仕組み、A+コンテンツ等)
5. "Qoo10" (メガ割の仕組み、共同購入など)
6. "TikTokshop" (動画コマースの仕組みやアフィリエイト連携など)

【生成ルール】
- 各テーマにつき、manualを最低1〜2個、quizを最低2個、case_studyを最低1個生成してください。
- manualの `content` は、Markdown形式をフル活用し（見出し `###`、太字 `**`、箇条書き `-` など）、非常に読みやすく充実した数十行〜百行程度の深い解説にしてください。
- case_studyの `example_solution` も同様にMarkdownをフル活用して構造的に詳しく書いてください。
- すべての出力において `theme` は上記で指定された文字列と一言一句完全に一致させてください。
- 出力は純粋なJSON配列のみとしてください。Markdownコードブロック(```json)は含めないでください。

【JSON構造の例】
[
    {
        "manual": {
            "title": "EC売上の方程式「売上＝アクセス数 × CVR × 客単価」の徹底解剖",
            "theme": "EC運営基礎知識",
            "category": "基礎理論・KPI",
            "content": "### 売上の方程式とは...\n\n- **アクセス数（Traffic）**...\n- **コンバージョン率（CVR）**...\n- **客単価（AOV）**...\n\n### 改善の順番\n...",
            "original_source": "自社オリジナル作成知識",
            "tags": ["KPI", "売上方程式", "基礎", "CVR"]
        }
    },
    {
        "quiz": {
            "theme": "楽天市場",
            "question": "楽天市場における「RPP広告」の正式名称は何でしょうか？",
            "options": ["Rakuten Point Promotion", "Rakuten Performance Program", "Rakuten Promotion Platform", "Rakuten Pay Per click"],
            "correct_answer": 2,
            "explanation": "RPPはRakuten Promotion Platformの略で、ユーザーの検索キーワード等に連動して表示される検索連動型広告（クリック課金型）です。",
            "original_source": "自社オリジナル作成知識"
        }
    },
    {
        "case_study": {
            "title": "【Amazon】カートボックス獲得率が低下した商品のテコ入れ",
            "theme": "Amazon",
            "scenario": "クライアントのAmazon店舗で、主力商品のカートボックス獲得率が先週の95%から40%に急落し、売上が半減しています。競合による相乗り出品が増加しているようです。",
            "question": "カートボックスを再獲得および防衛するために、どのような要因を確認し、どのような対策を打つべきか、優先順位をつけて回答してください。",
            "evaluation_rubric": ["価格競争力の確認が含まれているか", "FBAの活用や配送品質（プライム設定）に言及しているか", "アカウント健全性・出品者評価への言及があるか"],
            "example_solution": "### カートボックス獲得の主要因の確認\n1. **販売価格とポイント**...\n2. **配送オプション（FBA）**...\n...",
            "original_source": "自社オリジナル作成知識"
        }
    }
]
"""

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
    
    # Load existing to append
    manuals = []
    quizzes = []
    cases = []
    
    # Overwrite completely or prepend? The user wants fundamentals PRORITIZED.
    # Let's prepend them so they appear at the top.
    
    for parsed in parsed_array:
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

    # Prepend
    manuals.extend(existing_manuals)
    quizzes.extend(existing_quizzes)
    cases.extend(existing_cases)

    with open(os.path.join(DATA_DIR, 'manuals.json'), 'w', encoding='utf-8') as f:
        json.dump(manuals, f, ensure_ascii=False, indent=4)
    with open(os.path.join(DATA_DIR, 'quizzes.json'), 'w', encoding='utf-8') as f:
        json.dump(quizzes, f, ensure_ascii=False, indent=4)
    with open(os.path.join(DATA_DIR, 'cases.json'), 'w', encoding='utf-8') as f:
        json.dump(cases, f, ensure_ascii=False, indent=4)
        
    print(f"Generated {len(parsed_array)} foundational items!")

if __name__ == "__main__":
    generate_fundamentals()

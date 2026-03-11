import os
import json

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'data')

ALLOWED_THEMES = ["EC業界知識", "EC運営基礎知識", "楽天市場", "ヤフーショッピング", "Amazon", "Qoo10", "TikTokshop"]

def load_data(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_manuals_schema():
    manuals = load_data('manuals.json')
    for m in manuals:
        assert 'id' in m
        assert 'title' in m
        assert 'theme' in m, f"Manual lacks theme: {m.get('title')}"
        assert m['theme'] in ALLOWED_THEMES, f"Invalid theme {m.get('theme')}"
        assert 'category' in m
        assert 'content' in m
        assert 'original_source' in m, f"Manual {m.get('title')} lacks original_source"

def test_quizzes_schema():
    quizzes = load_data('quizzes.json')
    for q in quizzes:
        assert 'id' in q
        assert 'theme' in q, f"Quiz lacks theme: {q.get('question')}"
        assert q['theme'] in ALLOWED_THEMES, f"Invalid theme {q.get('theme')}"
        assert 'question' in q
        assert 'options' in q
        assert len(q['options']) == 4
        assert 'correct_answer' in q
        assert 'explanation' in q
        assert 'original_source' in q, f"Quiz {q.get('question')} lacks original_source"

def test_cases_schema():
    cases = load_data('cases.json')
    for c in cases:
        assert 'id' in c
        assert 'title' in c
        assert 'theme' in c, f"Case lacks theme: {c.get('title')}"
        assert c['theme'] in ALLOWED_THEMES, f"Invalid theme {c.get('theme')}"
        assert 'scenario' in c
        assert 'question' in c
        assert 'evaluation_rubric' in c
        assert len(c['evaluation_rubric']) > 0, "No rubrics found"
        assert 'example_solution' in c
        assert 'original_source' in c, f"Case {c.get('title')} lacks original_source"

def test_news_schema():
    news = load_data('news.json')
    for n in news:
        assert 'id' in n
        assert 'title' in n
        assert 'summary' in n
        assert 'original_source' in n, f"News {n.get('title')} lacks original_source"
        assert 'date' in n

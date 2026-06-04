import json
import os
import re

# ── 경로 설정 ──────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR   = os.path.join(BASE_DIR, "docs")
TEMPLATE   = os.path.join(BASE_DIR, "template.html")
STUDENTS   = os.path.join(BASE_DIR, "students.json")

os.makedirs(DOCS_DIR, exist_ok=True)

# ── 헬퍼 ──────────────────────────────────────────────
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def load_template():
    with open(TEMPLATE, encoding="utf-8") as f:
        return f.read()

SECTION_META = {
    "TEST": {"label": "📘 Chapter TEST",         "badge": "TEST"},
    "PLUS": {"label": "📗 실전문제 PLUS",          "badge": "PLUS"},
    "HARD": {"label": "🔴 고난도 문제",            "badge": "HARD"},
    "MB":   {"label": "📙 내신대비 실전문제",        "badge": "MB"},
}

# ── HTML 생성 함수 ────────────────────────────────────
def render_option_list(options, answer_str):
    """보기 목록 렌더링. 정답 번호에 correct 클래스 추가."""
    if not options:
        return ""
    numerals = ["①","②","③","④","⑤"]
    html = '<ul class="options">'
    for i, opt in enumerate(options):
        num = numerals[i] if i < len(numerals) else str(i+1)
        css = ""
        if num in answer_str or str(i+1) in answer_str:
            css = " correct"
        # 밑줄 마크다운 처리
        opt_html = re.sub(r'<u>(.*?)</u>', r'<u>\1</u>', opt)
        html += f'<li class="{css.strip()}">{num} {opt_html}</li>'
    html += "</ul>"
    return html

def render_explanation(explanation):
    if not explanation:
        return ""
    html = '<ul class="exp-list">'
    for key, val in explanation.items():
        css = "correct-exp" if "✓" in val else ("wrong-exp" if "✗" in val else "")
        html += f'<li class="{css}"><strong>{key}</strong> {val}</li>'
    html += "</ul>"
    return html

def render_card(q_num, q_data, section_key):
    badge_class = f"badge-{section_key}"
    badge_label = SECTION_META.get(section_key, {}).get("badge", section_key)

    content_html = ""
    if q_data.get("content"):
        content_html = f'<div class="q-box">{q_data["content"]}</div>'

    options_html = render_option_list(q_data.get("options", []), q_data.get("answer", ""))

    answer_val = q_data.get("answer", "")
    answer_html = f'''
    <div class="answer-row">
      <span class="label">정답</span>
      <span class="val">{answer_val}</span>
    </div>'''

    hint_html = ""
    if q_data.get("hint"):
        hint_html = f'''
    <div class="hint-box">
      <strong>개념 힌트</strong>
      {q_data["hint"]}
    </div>'''

    exp_inner = render_explanation(q_data.get("explanation", {}))
    exp_html = f'''
    <details class="explanation">
      <summary>▶ 상세 해설 보기</summary>
      {exp_inner}
    </details>''' if exp_inner else ""

    return f'''
<div class="card">
  <div class="card-inner">
    <div class="card-header">
      <span class="q-num">Q.{q_num}</span>
      <span class="badge {badge_class}">{badge_label}</span>
    </div>
    <div class="card-body">
      <p class="q-text">{q_data.get("q","")}</p>
      {content_html}
      {options_html}
      {answer_html}
      {hint_html}
      {exp_html}
    </div>
  </div>
</div>'''

def build_sections_html(wrong_nums, questions_data):
    sections = questions_data.get("sections", {})
    html = ""
    for sec_key, sec_data in sections.items():
        matching = {
            num: q
            for num, q in sec_data.get("questions", {}).items()
            if int(num) in wrong_nums
        }
        if not matching:
            continue
        label = SECTION_META.get(sec_key, {}).get("label", sec_key)
        html += f'<div class="section-title">{label} — {len(matching)}문항</div>\n'
        for num, q in matching.items():
            html += render_card(num, q, sec_key)
    return html

# ── 메인 빌드 루프 ─────────────────────────────────────
students = load_json(STUDENTS)
template = load_template()

# index.html 생성 (링크 목록)
index_rows = ""

for student in students:
    name        = student["name"]
    date        = student["date"]
    chapter     = student["chapter"]
    wrong_nums  = set(student.get("wrong", []))
    q_file      = os.path.join(BASE_DIR, student["questions_file"])

    if not os.path.exists(q_file):
        print(f"[SKIP] {name}: {q_file} 없음")
        continue

    questions_data = load_json(q_file)
    sections_html  = build_sections_html(wrong_nums, questions_data)

    html = template
    html = html.replace("{{STUDENT_NAME}}", name)
    html = html.replace("{{CHAPTER}}", chapter)
    html = html.replace("{{DATE}}", date)
    html = html.replace("{{WRONG_COUNT}}", str(len(wrong_nums)))
    html = html.replace("{{SECTIONS_HTML}}", sections_html)

    # 파일명: URL-safe (한글 그대로 저장, gh-pages는 UTF-8 지원)
    filename = f"{name}.html"
    out_path = os.path.join(DOCS_DIR, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] {name} → docs/{filename}")

    index_rows += f'<li><a href="{filename}">{name}</a> — {chapter} ({date}) · {len(wrong_nums)}문항</li>\n'

# index.html
index_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>오답 피드백 목록</title>
<style>
  body {{ font-family: 'Noto Sans KR', sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px; }}
  h1 {{ color: #5b4fcf; margin-bottom: 20px; }}
  ul {{ list-style: none; padding: 0; }}
  li {{ padding: 12px 16px; border-radius: 10px; margin-bottom: 8px; background: #f7f6fb; border-left: 4px solid #5b4fcf; }}
  a {{ color: #5b4fcf; font-weight: 700; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<h1>📝 오답 피드백 목록</h1>
<ul>
{index_rows}
</ul>
</body>
</html>"""

with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)
print("[OK] index.html 생성 완료")
print(f"\n총 {len(students)}명 처리 완료!")

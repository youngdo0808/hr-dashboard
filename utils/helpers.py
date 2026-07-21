"""utils/helpers.py — 공통 렌더링 헬퍼 함수 모음 (badges, flags, bullet lists 등)"""
import re

FLAG_MAP = {
    "국내": "🇰🇷", "국내(영)": "🇰🇷", "글로벌": "🌍", "글로벌(EU)": "🇪🇺",
    "APAC": "🌏", "미국": "🇺🇸", "EU": "🇪🇺",
}


def flag_for_region(region: str) -> str:
    return FLAG_MAP.get(str(region), "🌍")


def flatten_html(html: str) -> str:
    """여러 줄로 작성된 HTML을 한 줄로 압축한다.
    Streamlit의 알려진 버그(GH #859) 때문에 unsafe_allow_html=True로 넘기는
    멀티라인 문자열은 첫 줄 이후부터 그대로 텍스트로 노출될 수 있다.
    태그 사이 줄바꿈/들여쓰기는 렌더링에 영향이 없으므로, 항상 한 줄로 합쳐서
    st.markdown에 넘기면 이 문제를 완전히 피할 수 있다."""
    return " ".join(line.strip() for line in html.splitlines() if line.strip())


def bullets_html(points, css_class="news-bullets"):
    if not points:
        return ""
    items = "".join(f"<li>{p}</li>" for p in points if str(p).strip())
    return f"<ul class='{css_class}'>{items}</ul>"


def badge(text, bg, color, border=None):
    border_css = f"border:1.5px solid {border};" if border else ""
    return f"<span class='badge' style='background:{bg};color:{color};{border_css}'>{text}</span>"


def trust_badge(trust: dict):
    color = trust.get("color", "#64748B")
    return badge(trust.get("grade", ""), f"{color}15", color, f"{color}40")


def sentiment_badge(row):
    color = row.get("sent_color", "#64748B")
    return badge(f"{row.get('sent_emoji', '')} {row.get('sentiment', '')}", f"{color}15", color, f"{color}40")


def plain_badge(text):
    return badge(text, "#F1F5F9", "#374151")


def category_badge(category: str, cfg: dict):
    icon = cfg.get("icon", "🏷️")
    color = cfg.get("color", "#4F46E5")
    short = category.split("/")[0].strip()
    return badge(f"{icon} {short}", f"{color}12", color, f"{color}35")


_SENT_END = (".", "!", "?", "다", "요", ")", "」", "』", '"', "다.", "요.", "다!",
             "요!", "습니다", "합니다", "됩니다", "있습니다", "없습니다", "입니다")


def sentence_bullets(text: str, max_bullets: int = 3) -> list:
    """원문을 완전한 문장 단위로만 쪼개 불릿 리스트로 만든다. 잘린 문장은 절대 포함하지 않는다."""
    text = (text or "").strip()
    if not text:
        return []
    sentences = [s.strip() for s in re.split(r"(?<=[.!?다요])\s+", text) if s.strip()]
    if not sentences:
        return [text] if text.endswith(_SENT_END) else []
    if len(sentences) > 1 and not sentences[-1].endswith(_SENT_END):
        sentences = sentences[:-1]
    return sentences[:max_bullets] if sentences else []

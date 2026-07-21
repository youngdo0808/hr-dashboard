import html as _html
import re
import streamlit as st

from utils.helpers import bullets_html, trust_badge, sentiment_badge, plain_badge, flag_for_region, category_badge, flatten_html
from services.summarizer import get_structured_summary
from services.fetcher import CATEGORY_CONFIG


def _has_korean(text: str) -> bool:
    return bool(re.search(r'[가-힣]', text or ''))


def render_news_card(row, ai_on: bool, key_prefix: str, idx: int):
    lang = st.session_state.get("lang", "ko")

    trust = row.get("trust", {"grade": "뉴스 집계 / Aggregator", "color": "#64748B"})
    is_hot = row.get("is_hot", False)
    is_report = bool(row.get("tag", ""))
    hot_html = '<span class="hot-badge">HOT</span>' if is_hot else ""
    tag_html = f'<div class="report-tag">🏛️ {row.get("tag", "")}</div>' if is_report else ""

    cfg = CATEGORY_CONFIG.get(row.get("category", ""), {"color": "#4F46E5", "icon": "🏷️"})
    flag = flag_for_region(row.get("region", ""))

    title_ko = row.get("title_ko") or row.get("title", "")
    # Use explicit title_en if provided; fall back to title only when it is not Korean
    _raw_title = row.get("title", "")
    title_en = row.get("title_en") or (_raw_title if not _has_korean(_raw_title) else "")
    region_label = row.get("region", "")

    if lang == "en":
        primary_title = title_en if title_en else title_ko
        secondary_title = title_ko if (title_ko and title_ko.strip() != title_en.strip() and _has_korean(title_ko)) else ""
    else:
        primary_title = title_ko
        secondary_title = title_en if (title_en and title_en.strip() != title_ko.strip() and not _has_korean(title_en)) else ""

    struct_all = get_structured_summary(
        str(row.get("title", "")), str(row.get("description", "")),
        str(row.get("category", "")), ai_on,
    )
    struct = struct_all.get(lang, struct_all.get("ko", {}))

    if lang == "en":
        label_points = "📌 Key Messages"
        label_impact = "💼 Business Impact"
        label_insight = "💡 HR Insights"
        label_action = "⚡ Key Takeaways"
    else:
        label_points = "📌 핵심 메시지 / Key Messages"
        label_impact = "💼 비즈니스 영향 / Business Impact"
        label_insight = "💡 HR 시사점 / HR Insights"
        label_action = "⚡ 핵심 실행 과제 / Key Takeaways"

    secondary_html = f'<div class="news-title-en">{secondary_title}</div>' if secondary_title else ""
    safe_url = _html.escape(str(row.get("url", "#")), quote=True)

    card_html = (
        f'<div class="news-card" style="border-left:4px solid {cfg["color"]}">{hot_html}{tag_html}'
        f'<div class="news-title"><a href="{safe_url}" target="_blank" rel="noopener" '
        f'style="color:inherit;text-decoration:none">{primary_title}</a></div>'
        f'{secondary_html}'
        f'<div class="news-meta">'
        f'{trust_badge(trust)}'
        f'{sentiment_badge(row)}'
        f'{category_badge(row.get("category", ""), cfg)}'
        f'{plain_badge(row.get("source", ""))}'
        f'{plain_badge(f"{flag} {region_label}")}'
        f'{plain_badge(row.get("published_str", ""))}'
        f'</div>'
        f'<div class="news-block">'
        f'<div class="news-block-label">{label_points}</div>'
        f'{bullets_html(struct.get("points", []))}'
        f'</div>'
        f'<div class="news-block">'
        f'<div class="news-block-label">{label_impact}</div>'
        f'<div class="news-block-text">{struct.get("impact", "")}</div>'
        f'</div>'
        f'<div class="news-block">'
        f'<div class="news-block-label">{label_insight}</div>'
        f'<div class="news-block-text">{struct.get("insight", "")}</div>'
        f'</div>'
        f'<div class="news-block">'
        f'<div class="news-block-label">{label_action}</div>'
        f'<div class="news-block-text">{struct.get("action", "")}</div>'
        f'</div>'
        f'<a class="read-original" href="{safe_url}" target="_blank" rel="noopener">📎 Read Original Article ↗</a>'
        f'</div>'
    )
    st.markdown(flatten_html(card_html), unsafe_allow_html=True)

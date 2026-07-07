import streamlit as st

from utils.helpers import bullets_html, trust_badge, sentiment_badge, plain_badge, flag_for_region, category_badge, flatten_html
from services.summarizer import get_structured_summary
from services.fetcher import CATEGORY_CONFIG


def render_news_card(row, ai_on: bool, key_prefix: str, idx: int):
    trust = row.get("trust", {"grade": "뉴스 집계 / Aggregator", "color": "#64748B"})
    is_hot = row.get("is_hot", False)
    is_report = bool(row.get("tag", ""))
    hot_html = '<span class="hot-badge">HOT</span>' if is_hot else ""
    tag_html = f'<div class="report-tag">🏛️ {row.get("tag", "")}</div>' if is_report else ""

    cfg = CATEGORY_CONFIG.get(row.get("category", ""), {"color": "#4F46E5", "icon": "🏷️"})
    flag = flag_for_region(row.get("region", ""))

    title_ko = row.get("title_ko") or row.get("title", "")
    title_en = row.get("title", "")
    show_en_title = bool(title_en) and title_en.strip() != title_ko.strip()
    region_label = row.get("region", "")

    # 4-블록 구조 — AI 또는 규칙 기반, 절대 빈 값/중간 절단 없음
    struct = get_structured_summary(
        str(row.get("title", "")), str(row.get("description", "")),
        str(row.get("category", "")), ai_on,
    ).get("ko", {})

    en_title_html = f'<div class="news-title-en">{title_en}</div>' if show_en_title else ""

    card_html = (
        f'<div class="news-card" style="border-left:4px solid {cfg["color"]}">{hot_html}{tag_html}'
        f'<div class="news-title"><a href="{row["url"]}" target="_blank" rel="noopener" '
        f'style="color:inherit;text-decoration:none">{title_ko}</a></div>'
        f'{en_title_html}'
        f'<div class="news-meta">'
        f'{trust_badge(trust)}'
        f'{sentiment_badge(row)}'
        f'{category_badge(row.get("category", ""), cfg)}'
        f'{plain_badge(row.get("source", ""))}'
        f'{plain_badge(f"{flag} {region_label}")}'
        f'{plain_badge(row.get("published_str", ""))}'
        f'</div>'
        f'<div class="news-block">'
        f'<div class="news-block-label">📌 Key Messages / 핵심 메시지</div>'
        f'{bullets_html(struct.get("points", []))}'
        f'</div>'
        f'<div class="news-block">'
        f'<div class="news-block-label">💼 Business Impact / 비즈니스 영향</div>'
        f'<div class="news-block-text">{struct.get("impact", "")}</div>'
        f'</div>'
        f'<div class="news-block">'
        f'<div class="news-block-label">💡 HR Insights / HR 시사점</div>'
        f'<div class="news-block-text">{struct.get("insight", "")}</div>'
        f'</div>'
        f'<div class="news-block">'
        f'<div class="news-block-label">⚡ Key Takeaways / 핵심 실행 과제</div>'
        f'<div class="news-block-text">{struct.get("action", "")}</div>'
        f'</div>'
        f'<a class="read-original" href="{row["url"]}" target="_blank" rel="noopener">📎 Read Original Article ↗</a>'
        f'</div>'
    )
    st.markdown(flatten_html(card_html), unsafe_allow_html=True)

"""
components/business_insights.py
Business Insights tab — Physical AI · Semiconductor · AI Strategy · Digital Transformation.
Sources: HBR · MIT Tech Review · Wharton · BCG (live) + 9 curated entries (always shown).
Fully localized based on the language toggle.
"""
import html as _html
import streamlit as st
import pandas as pd

from utils.helpers import flatten_html, trust_badge, plain_badge, flag_for_region
from services.fetcher import get_trust

TOPIC_CONFIG = {
    "all":                    {"ko": "전체",        "en": "All Topics",            "icon": "🌐"},
    "ai_strategy":            {"ko": "AI 전략",     "en": "AI Strategy",           "icon": "🤖"},
    "physical_ai":            {"ko": "Physical AI", "en": "Physical AI",           "icon": "⚡"},
    "semiconductor":          {"ko": "반도체",       "en": "Semiconductor",         "icon": "🔬"},
    "digital_transformation": {"ko": "디지털 전환", "en": "Digital Transformation", "icon": "🌐"},
    "general":                {"ko": "혁신·비즈니스","en": "Innovation & Business", "icon": "💡"},
}


def _bi_curated_card(row: dict, lang: str) -> str:
    topic = row.get("topic", "general")
    tc = TOPIC_CONFIG.get(topic, TOPIC_CONFIG["general"])

    if lang == "en":
        title   = row.get("title",      row.get("title_ko", ""))
        summary = row.get("summary_en") or row.get("summary_ko") or row.get("description", "")
        insight = row.get("insight_en") or row.get("insight_ko", "")
        action  = row.get("action_en")  or row.get("action_ko",  "")
        lbl1 = "Key Business Insight"
        lbl2 = "HR & Workforce Implications"
        lbl3 = "Recommended Action"
        topic_label = f'{tc["icon"]} {tc["en"]}'
    else:
        title   = row.get("title_ko") or row.get("title", "")
        summary = row.get("summary_ko") or row.get("summary_en") or row.get("description", "")
        insight = row.get("insight_ko") or row.get("insight_en", "")
        action  = row.get("action_ko")  or row.get("action_en",  "")
        lbl1 = "핵심 비즈니스 인사이트"
        lbl2 = "HR · 인력 영향"
        lbl3 = "권고 실행 과제"
        topic_label = f'{tc["icon"]} {tc["ko"]}'

    source = row.get("source", "")
    url    = _html.escape(str(row.get("url", "#")), quote=True)
    pub    = row.get("published_str", "")
    pub_part = f" · {pub}" if pub and pub not in ("날짜 미상", source) else ""

    return (
        f'<div class="bi-card">'
        f'<div class="bi-topic-tag">{topic_label}</div>'
        f'<div class="bi-title">{title}</div>'
        f'<div class="bi-row"><div class="bi-label">{lbl1}</div><div class="bi-text">{summary}</div></div>'
        f'<div class="bi-row"><div class="bi-label">{lbl2}</div><div class="bi-text">{insight}</div></div>'
        f'<div class="bi-row"><div class="bi-label">{lbl3}</div><div class="bi-text">{action}</div></div>'
        f'<div class="bi-source">'
        f'<span class="bi-source-name">{source}</span>{pub_part}'
        f'<a href="{url}" target="_blank" rel="noopener" '
        f'style="color:#93C5FD;text-decoration:none;margin-left:12px">Read Original ↗</a>'
        f'</div></div>'
    )


def _bi_live_card(row: dict, ai_on: bool, lang: str):
    from utils.helpers import bullets_html, sentiment_badge, category_badge
    from services.summarizer import get_structured_summary
    from services.fetcher import CATEGORY_CONFIG

    topic = row.get("topic", "general")
    tc = TOPIC_CONFIG.get(topic, TOPIC_CONFIG["general"])
    topic_label = f'{tc["icon"]} {tc["en"] if lang == "en" else tc["ko"]}'
    topic_color = "#1D4ED8"

    trust = row.get("trust", {"grade": "뉴스 집계 / Aggregator", "color": "#64748B"})
    title_raw = row.get("title", "")
    flag = flag_for_region(row.get("region", ""))

    struct_all = get_structured_summary(
        str(row.get("title", "")),
        str(row.get("description", "")),
        str(row.get("category", "")),
        ai_on,
    )
    struct = struct_all.get(lang, struct_all.get("en", {}))

    if lang == "en":
        lbl_pts    = "📌 Key Insights"
        lbl_impact = "💼 Business Impact"
        lbl_hr     = "💡 HR Perspective"
        lbl_action = "⚡ Recommended Action"
    else:
        lbl_pts    = "📌 핵심 인사이트"
        lbl_impact = "💼 비즈니스 영향"
        lbl_hr     = "💡 HR 관점"
        lbl_action = "⚡ 권고 실행 과제"

    cfg = CATEGORY_CONFIG.get(row.get("category", ""), {"color": "#1D4ED8", "icon": "💼"})
    safe_url = _html.escape(str(row.get("url", "#")), quote=True)
    region_val = row.get("region", "")

    card_html = (
        f'<div class="news-card" style="border-left:4px solid {topic_color}">'
        f'<div class="report-tag" style="background:linear-gradient(90deg,#1D4ED8,#2563EB)">'
        f'{topic_label}</div>'
        f'<div class="news-title">'
        f'<a href="{safe_url}" target="_blank" rel="noopener" style="color:inherit;text-decoration:none">'
        f'{title_raw}</a></div>'
        f'<div class="news-meta">'
        f'{trust_badge(trust)}'
        f'{plain_badge(row.get("source", ""))}'
        f'{plain_badge(f"{flag} {region_val}")}'
        f'{plain_badge(row.get("published_str",""))}'
        f'</div>'
        f'<div class="news-block"><div class="news-block-label">{lbl_pts}</div>'
        f'{bullets_html(struct.get("points", []))}</div>'
        f'<div class="news-block"><div class="news-block-label">{lbl_impact}</div>'
        f'<div class="news-block-text">{struct.get("impact","")}</div></div>'
        f'<div class="news-block"><div class="news-block-label">{lbl_hr}</div>'
        f'<div class="news-block-text">{struct.get("insight","")}</div></div>'
        f'<div class="news-block"><div class="news-block-label">{lbl_action}</div>'
        f'<div class="news-block-text">{struct.get("action","")}</div></div>'
        f'<a class="read-original" href="{safe_url}" target="_blank" rel="noopener">'
        f'📎 Read Original Article ↗</a>'
        f'</div>'
    )
    st.markdown(flatten_html(card_html), unsafe_allow_html=True)


def render_business_insights_page(ai_on: bool):
    from components.hero import section_head
    from services.fetcher import load_business_insights
    from services.processor import enrich

    lang = st.session_state.get("lang", "ko")

    spinner_msg = ("Loading business intelligence..." if lang == "en"
                   else "비즈니스 인텔리전스 로딩 중...")
    with st.spinner(spinner_msg):
        df = load_business_insights()

    if df.empty:
        st.info("No business insights available. Please refresh." if lang == "en"
                else "비즈니스 인사이트가 없습니다. 새로고침해 주세요.")
        return

    if lang == "en":
        section_head("💡", "Business Insights", "Strategic Intelligence Hub",
                     "Physical AI · Semiconductor · AI Strategy · Digital Transformation · Innovation")
    else:
        section_head("💡", "비즈니스 인사이트", "Business Insights",
                     "Physical AI · 반도체 · AI 전략 · 디지털 전환 · 글로벌 비즈니스 동향")

    topic_keys   = list(TOPIC_CONFIG.keys())
    topic_labels = [f'{TOPIC_CONFIG[t]["icon"]} {TOPIC_CONFIG[t]["en" if lang == "en" else "ko"]}'
                    for t in topic_keys]

    selected_label = st.radio(
        "bi_topic", topic_labels, horizontal=True,
        label_visibility="collapsed", key="bi_topic_filter",
    )
    selected_topic = topic_keys[topic_labels.index(selected_label)]

    filtered_df = df if selected_topic == "all" else (
        df[df["topic"] == selected_topic] if "topic" in df.columns else df)

    if filtered_df.empty:
        st.info("No content available for this topic." if lang == "en"
                else "해당 주제의 콘텐츠가 없습니다.")
        return

    curated_df = (filtered_df[filtered_df["tag"] == "Business Insight"]
                  if "tag" in filtered_df.columns else pd.DataFrame())
    live_df    = (filtered_df[filtered_df["tag"] != "Business Insight"]
                  if "tag" in filtered_df.columns else filtered_df)

    if not curated_df.empty:
        n = len(curated_df)
        if lang == "en":
            section_head("🏛️", "Curated Strategic Intelligence", "Executive Briefings",
                         f"McKinsey · HBR · Bloomberg · BCG · Deloitte — {n} insights")
        else:
            section_head("🏛️", "큐레이션 전략 인텔리전스", "Curated Strategic Intelligence",
                         f"McKinsey · HBR · Bloomberg · BCG · Deloitte — {n}건")
        cols = st.columns(2)
        for idx, (_, row) in enumerate(curated_df.reset_index(drop=True).iterrows()):
            with cols[idx % 2]:
                st.markdown(flatten_html(_bi_curated_card(dict(row), lang)), unsafe_allow_html=True)

    if not live_df.empty:
        n = len(live_df)
        live_enriched = enrich(live_df.copy())
        if lang == "en":
            section_head("📡", "Live Business Intelligence", "Real-Time Updates",
                         f"HBR · MIT Tech Review · Wharton · BCG — {n} articles")
        else:
            section_head("📡", "실시간 비즈니스 인텔리전스", "Live Business Intelligence",
                         f"HBR · MIT Tech Review · Wharton · BCG — {n}건")
        for _, row in live_enriched.reset_index(drop=True).iterrows():
            _bi_live_card(dict(row), ai_on, lang)

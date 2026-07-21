import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

sys.path.append(os.path.dirname(__file__))

from services.fetcher import load_all_news, CATEGORY_CONFIG
from services.processor import enrich
from services.summarizer import get_gemini_client
from services.signals import compute_signals
from components.hero import render_header, section_head, render_nav, go_to, render_footer
from components.metrics import render_signals_section
from components.news_card import render_news_card
from components.thinktank import render_thinktank_section, render_thinktank_full_page
from components.executive import render_executive_insight, render_exec_hot_stories
from components.business_insights import render_business_insights_page

st.set_page_config(page_title="AI HR Intelligence Dashboard", page_icon="🧠",
                    layout="wide", initial_sidebar_state="expanded")

with open(os.path.join(os.path.dirname(__file__), "styles", "style.css"), encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── 기본 상태값 ───────────────────────────────────────────
if "selected_cats" not in st.session_state:
    st.session_state["selected_cats"] = list(CATEGORY_CONFIG.keys())
if "sent_filter" not in st.session_state:
    st.session_state["sent_filter"] = ["긍정 / Positive", "중립 / Neutral", "부정 / Negative"]
if "ai_on" not in st.session_state:
    st.session_state["ai_on"] = get_gemini_client() is not None
if "lang" not in st.session_state:
    st.session_state["lang"] = "ko"
if "signal_filter" not in st.session_state:
    st.session_state["signal_filter"] = []
if "signal_label" not in st.session_state:
    st.session_state["signal_label"] = ""

# Re-use the already-initialised session value — avoids a duplicate google.genai import
gemini_ok = st.session_state["ai_on"]

# ── 사이드바 ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='text-align:center;padding:24px 0 18px;border-bottom:1px solid rgba(255,255,255,0.07);margin-bottom:18px'>"
        "<div style='font-size:2.4rem'>🧠</div>"
        "<div style='font-size:1.05rem;font-weight:900;color:#F8FAFC;margin-top:6px'>AI HR Intelligence</div>"
        "<div style='font-size:0.65rem;color:#475569;letter-spacing:0.12em;text-transform:uppercase;margin-top:4px'>Executive Dashboard</div>"
        "</div>", unsafe_allow_html=True)

    query = st.text_input("search", placeholder="🔍 검색 (예: 최저임금, AI hiring...)", label_visibility="collapsed")

    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;font-size:0.62rem;color:#94A3B8;"
        "letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px'>🌐 Language / 언어</div>",
        unsafe_allow_html=True,
    )
    lang_en = st.toggle(
        "English Mode",
        value=(st.session_state.get("lang", "ko") == "en"),
        key="lang_switch",
    )
    st.session_state["lang"] = "en" if lang_en else "ko"

    st.markdown("---")
    st.markdown(
        f"<div style='text-align:center;font-size:0.65rem;color:#475569;line-height:1.9'>"
        f"AI 요약: {'✅ Gemini 연결됨' if gemini_ok else '⚠️ Settings에서 API 키 확인'}<br>"
        f"{datetime.now().strftime('%Y.%m.%d %H:%M')}</div>", unsafe_allow_html=True)

# ── 상단 헤더 + 네비게이션 ─────────────────────────────────
render_header(gemini_ok)
page = render_nav()

# 영문 모드 배너
if st.session_state.get("lang") == "en":
    st.markdown(
        '<div class="lang-banner">🌐 <strong>English Mode</strong> — All content displayed in English. '
        'Toggle off in the sidebar to switch back to Korean.</div>',
        unsafe_allow_html=True,
    )

# ── 데이터 로드 ───────────────────────────────────────────
all_cats = tuple(CATEGORY_CONFIG.keys())
with st.spinner("HR 뉴스 수집 중... (최초 약 15~25초)"):
    raw_df = load_all_news(all_cats, "전체")

if raw_df.empty:
    st.error("❌ 데이터를 가져오지 못했습니다. 네트워크 또는 API 키(Settings)를 확인하세요.")
    st.stop()

df = enrich(raw_df.copy())

# 검색 필터
if query:
    mask = (df["title"].str.contains(query, case=False, na=False) |
            df["description"].str.contains(query, case=False, na=False) |
            df["source"].str.contains(query, case=False, na=False))
    df = df[mask]

# 카테고리/감성 필터
df_view = df[df["category"].isin(st.session_state["selected_cats"])]
df_view = df_view[df_view["sentiment"].isin(st.session_state["sent_filter"])]

# 시그널 필터 (Korea/Global 탭에서 적용)
signal_filter = st.session_state.get("signal_filter", [])
signal_label = st.session_state.get("signal_label", "")

if signal_filter:
    text_col = (df_view["title"].fillna("") + " " + df_view["description"].fillna("")).str.lower()
    sig_mask = text_col.apply(lambda t: any(kw.lower() in t for kw in signal_filter))
    korea_df = df_view[df_view["region"].str.startswith("국내", na=False) & (df_view["tag"] == "") & sig_mask]
    global_df = df_view[~df_view["region"].str.startswith("국내", na=False) & (df_view["tag"] == "") & sig_mask]
else:
    korea_df = df_view[df_view["region"].str.startswith("국내", na=False) & (df_view["tag"] == "")]
    global_df = df_view[~df_view["region"].str.startswith("국내", na=False) & (df_view["tag"] == "")]

thinktank_df = df_view[df_view["tag"].astype(str).str.len() > 0]
ai_on = st.session_state["ai_on"] and gemini_ok


def _render_card_list(sub_df, key_prefix, empty_msg):
    if sub_df.empty:
        st.info(empty_msg)
        return
    for idx, (_, row) in enumerate(sub_df.reset_index(drop=True).iterrows()):
        render_news_card(row, ai_on, key_prefix, idx)


def _signal_filter_badge(page_key: str):
    """활성 시그널 필터 배지와 초기화 버튼을 표시한다."""
    if not signal_filter:
        return
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(
            f'<div class="signal-filter-badge">🔍 필터 활성: {signal_label}</div>',
            unsafe_allow_html=True,
        )
    with c2:
        if st.button("× 초기화", key=f"clear_sig_{page_key}"):
            st.session_state["signal_filter"] = []
            st.session_state["signal_label"] = ""
            st.rerun()


# ══════════════════════════════════════════════════════════
# 🏠 DASHBOARD
# ══════════════════════════════════════════════════════════
if page == "dashboard":
    section_head("🌍", "Global Think Tank", "Today's Strategic Signals",
                 "McKinsey · Korn Ferry · Bloomberg · Deloitte · BCG 큐레이션 인사이트")
    render_thinktank_section(thinktank_df, limit=6, ai_on=ai_on)

    section_head("📈", "오늘의 HR 시그널", "Today's HR Signals",
                 "카드를 클릭하면 관련 뉴스로 이동 · Click a card to view related articles")
    render_signals_section(compute_signals(df_view))

    section_head("🧠", "Executive Insight", "Today's Briefing",
                 "오늘의 종합 분석 · HR Director Perspective · Tomorrow Watchlist")
    render_executive_insight(df_view, ai_on)
    render_exec_hot_stories(df_view)

    # Exec → 내부 뉴스 카드 이동 버튼
    _ec1, _ec2 = st.columns(2)
    with _ec1:
        st.button("🇰🇷 Korea 뉴스 카드 보기 →", key="exec_go_korea",
                  on_click=go_to, args=("korea",), use_container_width=True)
    with _ec2:
        st.button("🌍 Global 뉴스 카드 보기 →", key="exec_go_global",
                  on_click=go_to, args=("global",), use_container_width=True)

    section_head("🇰🇷", "Korea HR Highlights", "Korea", f"{len(korea_df)}건 수집됨")
    c1, c2 = st.columns([5, 1])
    with c2:
        st.button("See More →", key="see_more_korea", use_container_width=True,
                  on_click=go_to, args=("korea",))
    _render_card_list(korea_df.head(4), "dash_kr", "국내 뉴스가 없습니다. Settings에서 카테고리를 확인하세요.")

    section_head("🌍", "Global HR Highlights", "Global", f"{len(global_df)}건 수집됨")
    c1, c2 = st.columns([5, 1])
    with c2:
        st.button("See More →", key="see_more_global", use_container_width=True,
                  on_click=go_to, args=("global",))
    _render_card_list(global_df.head(4), "dash_gl", "글로벌 뉴스가 없습니다. Settings에서 카테고리를 확인하세요.")

# ══════════════════════════════════════════════════════════
# 🇰🇷 KOREA
# ══════════════════════════════════════════════════════════
elif page == "korea":
    _signal_filter_badge("korea")
    section_head("🇰🇷", "Korea HR News", "All Korea Articles", f"총 {len(korea_df)}건")
    _render_card_list(korea_df, "korea", "국내 뉴스가 없습니다. 새로고침하거나 Settings에서 카테고리를 확인하세요.")

# ══════════════════════════════════════════════════════════
# 🌍 GLOBAL
# ══════════════════════════════════════════════════════════
elif page == "global":
    _signal_filter_badge("global")
    section_head("🌍", "Global HR News", "All Global Articles", f"총 {len(global_df)}건")
    _render_card_list(global_df, "global", "글로벌 뉴스가 없습니다. 새로고침하거나 Settings에서 카테고리를 확인하세요.")

# ══════════════════════════════════════════════════════════
# 🏛️ THINK TANK
# ══════════════════════════════════════════════════════════
elif page == "thinktank":
    render_thinktank_full_page(thinktank_df, df_view, compute_signals(df_view), ai_on)

# ══════════════════════════════════════════════════════════
# 💡 BUSINESS INSIGHTS
# ══════════════════════════════════════════════════════════
elif page == "business":
    render_business_insights_page(ai_on)

# ══════════════════════════════════════════════════════════
# ⚙️ SETTINGS
# ══════════════════════════════════════════════════════════
elif page == "settings":
    section_head("⚙️", "설정", "Settings", "카테고리 · 감성 필터 · AI 요약 · 데이터 소스")

    st.markdown("#### 카테고리 / Category")
    cols = st.columns(len(CATEGORY_CONFIG))
    new_selected = []
    for col, cat in zip(cols, CATEGORY_CONFIG):
        with col:
            checked = st.checkbox(cat.split("/")[0].strip(), value=cat in st.session_state["selected_cats"], key=f"set_c_{cat}")
            if checked:
                new_selected.append(cat)
    st.session_state["selected_cats"] = new_selected or list(CATEGORY_CONFIG.keys())

    st.markdown("#### 감성 필터 / Sentiment Filter")
    st.session_state["sent_filter"] = st.multiselect(
        "감성", ["긍정 / Positive", "중립 / Neutral", "부정 / Negative"],
        default=st.session_state["sent_filter"], label_visibility="collapsed")

    st.markdown("#### AI 요약 / AI Summary")
    st.session_state["ai_on"] = st.toggle("Gemini AI로 Key Summary·Business Impact·HR Insight 생성",
                                           value=st.session_state["ai_on"], disabled=not gemini_ok)
    if not gemini_ok:
        st.caption("⚠️ .streamlit/secrets.toml에 GEMINI_API_KEY를 입력하면 AI 요약이 활성화됩니다. "
                   "키가 없어도 규칙 기반 요약이 항상 제공됩니다.")

    st.markdown("#### 데이터 소스 / Data Sources")
    st.markdown(
        "- **싱크탱크 / Think Tank**: McKinsey · Korn Ferry · Deloitte · BCG · Bloomberg · HBR\n"
        "- **공식기관 / Official**: 고용노동부 · ILO · OECD · WEF\n"
        "- **글로벌 미디어 / Global Media**: Reuters · CNBC · BBC · Fortune\n"
        "- **전문매체 / Specialist**: HR Dive · HR Executive · HR Grapevine · HR Morning · HR Gazette · HR Tech Feed\n"
        "- **국내 / Domestic**: 매일노동뉴스 · ZDNet Korea · Korea JoongAng Daily · Google News KR · Naver 뉴스 API\n"
        "- **APAC**: HR Daily · HR Katha · Korea Herald · Nikkei Asia\n"
    )

    st.markdown("#### 데이터 내보내기 / Export")
    exp_cols = ["published_str", "category", "sentiment", "is_hot", "title", "source", "region", "url", "description"]
    exp_cols = [c for c in exp_cols if c in df.columns]
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("CSV 다운로드", df[exp_cols].to_csv(index=False, encoding="utf-8-sig"),
                            "hr_intelligence.csv", "text/csv", use_container_width=True)
    with c2:
        st.download_button("JSON 다운로드", df[exp_cols].to_json(orient="records", force_ascii=False, indent=2),
                            "hr_intelligence.json", "application/json", use_container_width=True)

    st.markdown("---")
    st.caption(f"AI HR Intelligence Dashboard · Powered by Google Gemini 2.5 Flash · "
               f"Last updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

render_footer()

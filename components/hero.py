import streamlit as st
from datetime import datetime

from utils.helpers import flatten_html


def render_header(gemini_ok: bool, last_updated: str = ""):
    status_color = "#4ADE80" if gemini_ok else "#FCD34D"
    status_text = "Gemini Connected" if gemini_ok else "AI Summary Off"
    ts = last_updated or datetime.now().strftime("%Y.%m.%d %H:%M")
    html = f"""
    <div class="app-header">
        <div class="app-header-row">
            <div>
                <div class="app-title">AI <span>HR Intelligence</span> Dashboard</div>
                <div class="app-subtitle">Today's Strategic HR Signals · {ts}</div>
            </div>
            <div style="font-size:0.72rem;font-weight:700;color:{status_color};background:#0F172A;
                border-radius:20px;padding:6px 14px;white-space:nowrap;">● {status_text}</div>
        </div>
    </div>
    """
    st.markdown(flatten_html(html), unsafe_allow_html=True)


def section_head(icon: str, title_ko: str, title_en: str, sub: str = ""):
    html = f"""
    <div class="section-head">
        <div class="section-title">{icon} {title_ko} <span style="color:#94A3B8;font-weight:600;font-size:0.85rem">/ {title_en}</span></div>
        <div class="section-sub">{sub}</div>
    </div>
    <div class="section-divider"></div>
    """
    st.markdown(flatten_html(html), unsafe_allow_html=True)


NAV_ITEMS = [
    ("dashboard", "🏠 Dashboard"),
    ("korea", "🇰🇷 Korea"),
    ("global", "🌍 Global"),
    ("thinktank", "🏛️ Think Tank"),
    ("settings", "⚙️ Settings"),
]


def render_nav():
    """Executive Dashboard 스타일의 상단 세그먼트 네비게이션. st.session_state['page']를 사용해
    Dashboard의 'See More' 버튼 등에서 프로그래밍적으로 페이지를 전환할 수 있게 한다.
    주의: 위젯 key(nav_radio)에 이미 값이 있으면 index 인자는 무시되므로, index는 최초
    1회(키가 없을 때)만 넘기고 이후에는 session_state 값만으로 제어한다."""
    labels = [label for _, label in NAV_ITEMS]
    keys = [key for key, _ in NAV_ITEMS]
    if "page" not in st.session_state:
        st.session_state["page"] = "dashboard"
    if "nav_radio" not in st.session_state:
        st.session_state["nav_radio"] = dict(NAV_ITEMS)[st.session_state["page"]]

    st.markdown('<div class="nav-pill-wrap">', unsafe_allow_html=True)
    choice = st.radio("nav", labels, horizontal=True, label_visibility="collapsed", key="nav_radio")
    st.markdown("</div>", unsafe_allow_html=True)
    st.session_state["page"] = keys[labels.index(choice)]
    return st.session_state["page"]


def render_footer():
    html = f"""
    <div class="app-footer">
        <div class="footer-credit">
            Made by <span>Ella Youngeun Do</span> · 도영은 제작
        </div>
        <div class="footer-info">
            AI HR Intelligence Dashboard · Powered by Google Gemini<br>
            {datetime.now().strftime('%Y.%m.%d %H:%M')} KST
        </div>
    </div>
    """
    st.markdown(flatten_html(html), unsafe_allow_html=True)


def go_to(page_key: str):
    """다른 컴포넌트('See More' 버튼 등)에서 호출해 페이지를 전환한다.
    st.radio는 위젯 key(nav_radio)에 저장된 이전 선택값을 index보다 우선하므로,
    라벨 값도 함께 맞춰줘야 다음 렌더링에서 올바른 탭이 선택된다."""
    st.session_state["page"] = page_key
    label = dict(NAV_ITEMS).get(page_key)
    if label:
        st.session_state["nav_radio"] = label

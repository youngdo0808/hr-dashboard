import streamlit as st

from utils.helpers import flatten_html
from components.hero import NAV_ITEMS

_PAGE_LABELS = dict(NAV_ITEMS)


def _go_to_filtered(page_key: str, kw: list, label: str):
    """Navigate to a page and activate a signal keyword filter."""
    st.session_state["page"] = page_key
    st.session_state["nav_radio"] = _PAGE_LABELS.get(page_key, page_key)
    st.session_state["signal_filter"] = kw
    st.session_state["signal_label"] = label


def render_signals_section(signals: list):
    if not signals:
        st.info("표시할 시그널이 없습니다. / No signals available.")
        return

    cols = st.columns(len(signals))
    for col, s in zip(cols, signals):
        with col:
            # Metric card (visual)
            st.markdown(flatten_html(f"""
            <div class="metric-card">
                <div class="metric-icon">{s['icon']}</div>
                <div class="metric-num" style="color:{s.get('color','#0F172A')}">{s['count']}
                    <span class="metric-arrow" style="color:{s.get('color','#0F172A')}">{s.get('arrow','')}</span>
                </div>
                <div class="metric-label">{s['label']}</div>
                <div class="metric-label-ko">{s['label_ko']}</div>
            </div>
            """), unsafe_allow_html=True)

            # Click-through button → Korea page with filter
            label_full = f"{s['icon']} {s['label']} / {s['label_ko']}"
            st.button(
                "뉴스 보기 →",
                key=f"sig_{s.get('key', s['label'])}",
                on_click=_go_to_filtered,
                args=("korea", s.get("kw", []), label_full),
            )

import streamlit as st

from utils.helpers import flatten_html


def render_signals_section(signals: list):
    if not signals:
        st.info("표시할 시그널이 없습니다. / No signals available.")
        return
    cards_html = "".join(
        f"""<div class="metric-card">
            <div class="metric-icon">{s['icon']}</div>
            <div class="metric-num" style="color:{s.get('color', '#0F172A')}">{s['count']}
                <span class="metric-arrow" style="color:{s.get('color', '#0F172A')}">{s.get('arrow', '')}</span>
            </div>
            <div class="metric-label">{s['label']}</div>
            <div class="metric-label-ko">{s['label_ko']}</div>
        </div>"""
        for s in signals
    )
    st.markdown(flatten_html(f"<div class='metric-grid'>{cards_html}</div>"), unsafe_allow_html=True)

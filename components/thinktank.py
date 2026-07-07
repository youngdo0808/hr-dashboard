"""
components/thinktank.py
Think Tank dashboard card (hero section) + full Think Tank page renderer.
Full page: Weekly Trends / Emerging Signals / Future Outlook / Executive Recommendations / Action Items
"""
import streamlit as st

from components.executive import render_executive_insight
from utils.helpers import flatten_html


def render_thinktank_section(curated_df, limit: int = None):
    """Dashboard hero section: top N curated insights as premium cards."""
    if curated_df.empty:
        st.info("싱크탱크 인사이트가 없습니다. 새로고침해 주세요. / No think-tank insights available.")
        return
    if limit:
        curated_df = curated_df.head(limit)

    cols = st.columns(2)
    for idx, (_, row) in enumerate(curated_df.iterrows()):
        with cols[idx % 2]:
            html = f"""
            <div class="tt-card">
                <div class="tt-tag">🏛️ {row.get('tag', 'Think Tank')}</div>
                <div class="tt-title">{row.get('title_ko', row.get('title', ''))}</div>
                <div class="tt-row">
                    <div class="tt-label">Why it Matters</div>
                    <div class="tt-text">{row.get('summary_ko', '')}</div>
                </div>
                <div class="tt-row">
                    <div class="tt-label">Expected Impact</div>
                    <div class="tt-text">{row.get('action_ko', '')}</div>
                </div>
                <div class="tt-row">
                    <div class="tt-label">HR Perspective</div>
                    <div class="tt-text">{row.get('insight_ko', '')}</div>
                </div>
                <div class="tt-source">
                    <a href="{row.get('url','#')}" target="_blank" rel="noopener"
                       style="color:#93C5FD;text-decoration:none">
                        {row.get('source','')} — Read Original ↗
                    </a>
                </div>
            </div>
            """
            st.markdown(flatten_html(html), unsafe_allow_html=True)


def _analysis_card(label: str, emoji: str, items: list, item_color: str = "#374151"):
    """Render a structured analysis card with labelled bullet items."""
    items_html = "".join(
        f'<div class="tt-analysis-item">'
        f'<div class="tt-analysis-dot" style="background:{item_color}"></div>'
        f'<div style="color:{item_color}">{item}</div>'
        f'</div>'
        for item in items
    )
    html = f"""
    <div class="tt-analysis-card">
        <div class="tt-section-label">{emoji} {label}</div>
        {items_html}
    </div>
    """
    st.markdown(flatten_html(html), unsafe_allow_html=True)


def _action_card(label: str, emoji: str, items: list):
    """Render action items with checkbox-style rows."""
    items_html = "".join(
        f'<div class="tt-action-item">'
        f'<div class="tt-action-check">☐</div>'
        f'<div>{item}</div>'
        f'</div>'
        for item in items
    )
    html = f"""
    <div class="tt-analysis-card">
        <div class="tt-section-label">{emoji} {label}</div>
        {items_html}
    </div>
    """
    st.markdown(flatten_html(html), unsafe_allow_html=True)


def render_thinktank_full_page(curated_df, df_view, signals: list, ai_on: bool):
    """Full Think Tank page: Gartner/McKinsey-style strategic intelligence report."""

    # ── Weekly Trends ─────────────────────────────────────────────────────
    from components.hero import section_head
    section_head("📈", "Weekly Trends", "주간 HR 트렌드",
                 "이번 주 주요 HR 시그널 · 카테고리별 논의량 분석")

    if signals:
        trend_items = [
            f"<strong>{s['label']} / {s['label_ko']}</strong> — {s['count']}건 수집 "
            f"({'▲ 상승 신호' if s['direction'] == 'up' else '▼ 하락 신호'})"
            for s in signals
        ]
        _analysis_card("Weekly Trends / 주간 트렌드", "📈", trend_items, item_color="#2563EB")
    else:
        st.info("트렌드 데이터를 불러오는 중입니다. / Loading trend data...")

    # ── Emerging Signals ──────────────────────────────────────────────────
    section_head("📡", "Emerging Signals", "부상 신호",
                 "McKinsey · Korn Ferry · Deloitte · BCG 큐레이션 인사이트")

    if not curated_df.empty:
        cols = st.columns(2)
        for idx, (_, row) in enumerate(curated_df.iterrows()):
            with cols[idx % 2]:
                html = f"""
                <div class="tt-card">
                    <div class="tt-tag">🏛️ {row.get('tag', 'Think Tank')}</div>
                    <div class="tt-title">{row.get('title_ko', row.get('title', ''))}</div>
                    <div class="tt-row">
                        <div class="tt-label">Why it Matters</div>
                        <div class="tt-text">{row.get('summary_ko', '')}</div>
                    </div>
                    <div class="tt-row">
                        <div class="tt-label">Expected Impact</div>
                        <div class="tt-text">{row.get('action_ko', '')}</div>
                    </div>
                    <div class="tt-row">
                        <div class="tt-label">HR Perspective</div>
                        <div class="tt-text">{row.get('insight_ko', '')}</div>
                    </div>
                    <div class="tt-source">
                        <a href="{row.get('url','#')}" target="_blank" rel="noopener"
                           style="color:#93C5FD;text-decoration:none">
                            {row.get('source','')} — Read Original ↗
                        </a>
                    </div>
                </div>
                """
                st.markdown(flatten_html(html), unsafe_allow_html=True)
    else:
        st.info("큐레이션 인사이트가 없습니다. / No curated insights available.")

    # ── Future Outlook ────────────────────────────────────────────────────
    section_head("🔭", "Future Outlook", "미래 전망",
                 "AI·데이터 기반 HR 전망 · 내일의 인사 아젠다")

    if not curated_df.empty:
        outlook_items = []
        for _, row in curated_df.head(5).iterrows():
            insight = row.get("insight_ko") or row.get("insight_en") or ""
            if insight:
                src = row.get("source", "")
                outlook_items.append(f"[{src}] {insight}")
        if outlook_items:
            _analysis_card("Future Outlook / 미래 전망", "🔭", outlook_items, item_color="#4F46E5")
        else:
            st.info("전망 데이터를 생성 중입니다. / Generating outlook data...")
    else:
        st.info("전망 데이터를 생성 중입니다. / Generating outlook data...")

    # ── Executive Recommendations + Action Items ───────────────────────────
    section_head("🧠", "Executive Recommendations & Action Items",
                 "경영진 권고 사항 · 실행 과제",
                 "오늘의 데이터 기반 종합 분석 · HR Director Perspective")

    render_executive_insight(df_view, ai_on)

    # Aggregate action items from curated reports
    if not curated_df.empty:
        action_items = []
        for _, row in curated_df.iterrows():
            action = row.get("action_ko") or row.get("action_en") or ""
            if action:
                src = row.get("source", "")
                action_items.append(f"[{src}] {action}")
        if action_items:
            _action_card("Action Items / 실행 체크리스트", "✅", action_items)

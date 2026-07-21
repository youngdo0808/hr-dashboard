"""
components/thinktank.py
Think Tank dashboard card (hero section) + full Think Tank page renderer.
- CURATED_INSIGHTS (하드코딩): 하위 필드(insight_ko, action_ko 등) 완비
- Live RSS (McKinsey·HBR·WEF 등 자동 태깅): insight/action을 AI/규칙 기반으로 자동 생성
"""
import streamlit as st

from components.executive import render_executive_insight
from services.summarizer import get_structured_summary
from utils.helpers import flatten_html


def _enrich_row(row, ai_on: bool) -> dict:
    """Live RSS Think Tank 기사에 insight/action이 없으면 structured summary로 채운다."""
    if row.get("insight_ko") and row.get("action_ko"):
        return row  # 이미 완비된 큐레이션 인사이트
    struct = get_structured_summary(
        str(row.get("title", "")),
        str(row.get("description", "")),
        str(row.get("category", "")),
        ai_on,
    )
    enriched = dict(row)
    ko = struct.get("ko", {})
    en = struct.get("en", {})
    if not enriched.get("summary_ko"):
        enriched["summary_ko"] = row.get("description", "")
    if not enriched.get("summary_en"):
        enriched["summary_en"] = row.get("description", "")
    enriched["insight_ko"] = enriched.get("insight_ko") or ko.get("insight", "")
    enriched["insight_en"] = enriched.get("insight_en") or en.get("insight", "")
    enriched["action_ko"]  = enriched.get("action_ko")  or ko.get("action", "")
    enriched["action_en"]  = enriched.get("action_en")  or en.get("action", "")
    return enriched


def _tt_card_html(row, ai_on: bool = False) -> str:
    """Language-aware Think Tank card HTML (curated + live RSS 모두 지원)."""
    import html as _html
    row = _enrich_row(row, ai_on)
    lang = st.session_state.get("lang", "ko")

    if lang == "en":
        title   = row.get("title",      row.get("title_ko", ""))
        summary = row.get("summary_en", row.get("summary_ko", row.get("description", "")))
        insight = row.get("insight_en", row.get("insight_ko", ""))
        action  = row.get("action_en",  row.get("action_ko",  ""))
        lbl1, lbl2, lbl3 = "Why it Matters", "Expected Impact", "HR Perspective"
    else:
        title   = row.get("title_ko",   row.get("title", ""))
        summary = row.get("summary_ko", row.get("summary_en", row.get("description", "")))
        insight = row.get("insight_ko", row.get("insight_en", ""))
        action  = row.get("action_ko",  row.get("action_en",  ""))
        lbl1, lbl2, lbl3 = "Why it Matters / 중요성", "Expected Impact / 예상 영향", "HR Perspective / HR 관점"

    return (
        f'<div class="tt-card">'
        f'<div class="tt-tag">🏛️ {row.get("tag", "Think Tank")}</div>'
        f'<div class="tt-title">{title}</div>'
        f'<div class="tt-row"><div class="tt-label">{lbl1}</div><div class="tt-text">{summary}</div></div>'
        f'<div class="tt-row"><div class="tt-label">{lbl2}</div><div class="tt-text">{action}</div></div>'
        f'<div class="tt-row"><div class="tt-label">{lbl3}</div><div class="tt-text">{insight}</div></div>'
        f'<div class="tt-source">'
        f'<a href="{_html.escape(str(row.get("url", "#")), quote=True)}" target="_blank" rel="noopener" style="color:#93C5FD;text-decoration:none">'
        f'{row.get("source", "")} — Read Original ↗</a>'
        f'</div></div>'
    )


def render_thinktank_section(curated_df, limit: int = None, ai_on: bool = False):
    """Dashboard hero section: top N Think Tank cards (curated + live RSS)."""
    if curated_df.empty:
        st.info("싱크탱크 인사이트가 없습니다. 새로고침해 주세요. / No think-tank insights available.")
        return
    if limit:
        curated_df = curated_df.head(limit)

    cols = st.columns(2)
    for idx, (_, row) in enumerate(curated_df.iterrows()):
        with cols[idx % 2]:
            st.markdown(flatten_html(_tt_card_html(row, ai_on)), unsafe_allow_html=True)


def _analysis_card(label: str, emoji: str, items: list, item_color: str = "#374151"):
    items_html = "".join(
        f'<div class="tt-analysis-item">'
        f'<div class="tt-analysis-dot" style="background:{item_color}"></div>'
        f'<div style="color:{item_color}">{item}</div>'
        f'</div>'
        for item in items
    )
    html = f'<div class="tt-analysis-card"><div class="tt-section-label">{emoji} {label}</div>{items_html}</div>'
    st.markdown(flatten_html(html), unsafe_allow_html=True)


def _action_card(label: str, emoji: str, items: list):
    items_html = "".join(
        f'<div class="tt-action-item"><div class="tt-action-check">☐</div><div>{item}</div></div>'
        for item in items
    )
    html = f'<div class="tt-analysis-card"><div class="tt-section-label">{emoji} {label}</div>{items_html}</div>'
    st.markdown(flatten_html(html), unsafe_allow_html=True)


def render_thinktank_full_page(curated_df, df_view, signals: list, ai_on: bool):
    """Full Think Tank page: Gartner/McKinsey-style strategic intelligence report."""
    lang = st.session_state.get("lang", "ko")
    from components.hero import section_head

    # ── Weekly Trends ─────────────────────────────────────────────────────
    section_head("📈", "Weekly Trends", "주간 HR 트렌드",
                 "이번 주 주요 HR 시그널 · 카테고리별 논의량 분석")
    if signals:
        trend_items = [
            f"<strong>{s['label']} / {s['label_ko']}</strong> — {s['count']}건 수집 "
            f"({'▲ 상승 신호' if s.get('direction') == 'up' else '▼ 하락 신호'})"
            for s in signals
        ]
        _analysis_card("Weekly Trends / 주간 트렌드", "📈", trend_items, item_color="#2563EB")
    else:
        st.info("트렌드 데이터를 불러오는 중입니다. / Loading trend data...")

    # ── Emerging Signals ──────────────────────────────────────────────────
    section_head("📡", "Emerging Signals", "부상 신호",
                 "McKinsey · Korn Ferry · Deloitte · BCG · HBR · WEF 최신 인사이트")
    if not curated_df.empty:
        cols = st.columns(2)
        for idx, (_, row) in enumerate(curated_df.iterrows()):
            with cols[idx % 2]:
                st.markdown(flatten_html(_tt_card_html(row, ai_on)), unsafe_allow_html=True)
    else:
        st.info("큐레이션 인사이트가 없습니다. / No curated insights available.")

    # ── Future Outlook ────────────────────────────────────────────────────
    section_head("🔭", "Future Outlook", "미래 전망",
                 "AI·데이터 기반 HR 전망 · 내일의 인사 아젠다")
    if not curated_df.empty:
        outlook_items = []
        insight_key = "insight_en" if lang == "en" else "insight_ko"
        for _, row in curated_df.head(5).iterrows():
            enriched = _enrich_row(dict(row), ai_on)
            insight = enriched.get(insight_key) or enriched.get("insight_ko") or enriched.get("insight_en") or ""
            if insight:
                outlook_items.append(f"[{enriched.get('source', '')}] {insight}")
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

    if not curated_df.empty:
        action_items = []
        action_key = "action_en" if lang == "en" else "action_ko"
        for _, row in curated_df.iterrows():
            enriched = _enrich_row(dict(row), ai_on)
            action = enriched.get(action_key) or enriched.get("action_ko") or enriched.get("action_en") or ""
            if action:
                action_items.append(f"[{enriched.get('source', '')}] {action}")
        if action_items:
            _action_card("Action Items / 실행 체크리스트", "✅", action_items)

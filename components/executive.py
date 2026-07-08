"""
components/executive.py
McKinsey / Gartner / Deloitte 스타일 Executive Briefing.
Sections: Executive Summary · Key Risks · Emerging Trends · Tomorrow Watchlist · Recommended Actions
"""
import streamlit as st

from services.summarizer import get_gemini_client
from utils.helpers import flatten_html, flag_for_region


def _rule_based_briefing(df):
    if df.empty:
        return None
    top_cat = df["category"].value_counts().idxmax()
    top_cat_short = top_cat.split("/")[0].strip()
    pos_ratio = df["sentiment"].str.contains("긍정", na=False).mean() if "sentiment" in df else 0
    neg_ratio = df["sentiment"].str.contains("부정", na=False).mean() if "sentiment" in df else 0
    hot = df[df["is_hot"] == True].head(3) if "is_hot" in df.columns else df.head(3)
    hot_titles = [str(t) for t in hot["title"].tolist()]

    mood = "긍정적인 신호가 우세" if pos_ratio > neg_ratio else ("부정적 이슈가 다소 두드러짐" if neg_ratio > pos_ratio else "혼재된 신호")

    summary = (
        f"오늘 수집된 HR 뉴스 {len(df)}건 중 '{top_cat_short}' 관련 이슈가 가장 활발히 논의되고 있으며, "
        f"전반적인 톤은 {mood}입니다. "
        + (f"주목할 만한 이슈로는 「{hot_titles[0]}」 등이 있습니다." if hot_titles else "")
    )

    neg_articles = df[df["sentiment"].str.contains("부정", na=False)].head(3)
    risks = []
    if not neg_articles.empty:
        for _, r in neg_articles.iterrows():
            risks.append(f"'{r.get('category','').split('/')[0].strip()}' 영역 부정 신호 증가 — {str(r.get('title',''))[:60]}...")
    if not risks:
        risks = [
            f"'{top_cat_short}' 관련 규제 환경 변화에 따른 컴플라이언스 리스크",
            "핵심 인재 이탈 및 인재 확보 경쟁 심화 가능성",
        ]

    pos_cats = df[df["sentiment"].str.contains("긍정", na=False)]["category"].value_counts().head(2).index.tolist()
    trends = []
    for cat in pos_cats:
        trends.append(f"{cat.split('/')[0].strip()} 분야 긍정 모멘텀 형성 중")
    if not trends:
        trends = [
            "AI·HR테크 활용 조직의 채용 효율 향상 트렌드 가속",
            "유연근무·하이브리드 정책 고도화 수요 증가",
        ]

    watchlist = [
        f"'{top_cat_short}' 관련 후속 정책·발표 여부",
        "경쟁사의 유사 이슈 대응 방식",
        "고용노동부 등 규제기관 추가 가이드라인 발표 여부",
    ]
    actions = [
        "오늘 HOT 이슈를 팀 주간 회의 안건으로 공유하세요.",
        f"'{top_cat_short}' 카테고리의 자사 정책 현황을 1페이지로 정리해두세요.",
        "관련 부서(법무·재무 등)와 사전 정합성 체크를 진행하세요.",
    ]
    return {
        "summary": summary,
        "risks": risks,
        "trends": trends,
        "watchlist": watchlist,
        "actions": actions,
    }


@st.cache_data(ttl=3600, show_spinner=False)
def _ai_briefing(titles_categories: tuple):
    client = get_gemini_client()
    if not client:
        return None
    joined = "\n".join(f"- [{c}] {t}" for t, c in titles_categories[:25])
    prompt = f"""You are a McKinsey/Gartner-style HR research director writing a daily executive briefing
for a CHRO in Korea. Base your briefing ONLY on the news items below (do not invent unrelated facts).

News items:
{joined}

Respond ONLY in this exact format, in Korean, with complete sentences (never cut off mid-sentence):
SUMMARY: [2-3 sentence executive summary of today's overall HR news landscape]
RISK1: [Key risk #1 that HR leaders should be aware of today]
RISK2: [Key risk #2 that HR leaders should be aware of today]
TREND1: [Emerging trend #1 observed across today's news]
TREND2: [Emerging trend #2 observed across today's news]
WATCH1: [one thing to watch tomorrow]
WATCH2: [another thing to watch tomorrow]
WATCH3: [another thing to watch tomorrow]
ACTION1: [one concrete recommended action for HR leaders]
ACTION2: [another concrete recommended action]
ACTION3: [another concrete recommended action]"""
    try:
        from google.genai import types
        resp = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=1500,
                temperature=0.4,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        text = (resp.text or "").strip()
        out = {"summary": "", "risks": [], "trends": [], "watchlist": [], "actions": []}
        for line in text.splitlines():
            line = line.strip()
            up = line.upper()
            if up.startswith("SUMMARY:"):
                out["summary"] = line.split(":", 1)[1].strip()
            elif up.startswith("RISK"):
                out["risks"].append(line.split(":", 1)[1].strip())
            elif up.startswith("TREND"):
                out["trends"].append(line.split(":", 1)[1].strip())
            elif up.startswith("WATCH"):
                out["watchlist"].append(line.split(":", 1)[1].strip())
            elif up.startswith("ACTION"):
                out["actions"].append(line.split(":", 1)[1].strip())
        if not out["summary"]:
            return None
        return out
    except Exception:
        return None


def render_executive_insight(df, ai_on: bool):
    briefing = None
    if ai_on and not df.empty:
        pairs = tuple(zip(df["title"].tolist(), df["category"].tolist()))
        briefing = _ai_briefing(pairs)
    if not briefing:
        briefing = _rule_based_briefing(df)
    if not briefing:
        st.info("Executive Insight를 생성할 데이터가 없습니다. / No data available for Executive Insight.")
        return

    risk_html = "".join(f"<li>{r}</li>" for r in briefing.get("risks", []))
    trend_html = "".join(f"<li>{t}</li>" for t in briefing.get("trends", []))
    watch_html = "".join(f"<li>{w}</li>" for w in briefing.get("watchlist", []))
    action_html = "".join(f'<div class="exec-action">✅ {a}</div>' for a in briefing.get("actions", []))

    html = f"""
    <div class="exec-card">
        <div class="exec-title">🧠 Executive Brief — Today's Strategic Intelligence</div>

        <div class="exec-summary">{briefing['summary']}</div>

        <div class="exec-sub">⚠️ Key Risks / 핵심 리스크</div>
        <ul class="exec-risk">{risk_html}</ul>

        <div class="exec-sub">📡 Emerging Trends / 부상 트렌드</div>
        <ul class="exec-trend">{trend_html}</ul>

        <div class="exec-sub">👁 Tomorrow Watchlist / 내일 주시 사항</div>
        <ul class="exec-watch">{watch_html}</ul>

        <div class="exec-sub">✅ Recommended Actions / 권고 실행 과제</div>
        {action_html}
    </div>
    """
    st.markdown(flatten_html(html), unsafe_allow_html=True)


def render_exec_hot_stories(df):
    """Executive Brief 하단 — HOT 기사 4개를 컴팩트 링크로 표시."""
    if df is None or df.empty or "is_hot" not in df.columns:
        return
    hot = df[df["is_hot"] == True].head(4)
    if hot.empty:
        return

    items_html = ""
    for _, r in hot.iterrows():
        flag = flag_for_region(r.get("region", ""))
        raw_title = str(r.get("title", ""))
        title = raw_title[:78] + ("…" if len(raw_title) > 78 else "")
        url = r.get("url", "#")
        src = r.get("source", "")
        cat = str(r.get("category", "")).split("/")[0].strip()
        items_html += (
            f'<a class="exec-hot-link" href="{url}" target="_blank" rel="noopener">'
            f'<span class="exec-hot-flag">{flag}</span>'
            f'<span class="exec-hot-title">{title}</span>'
            f'<span class="exec-hot-src">{src} · {cat}</span>'
            f'</a>'
        )

    html = (
        f'<div class="exec-hot-box">'
        f'<div class="exec-hot-label">📎 오늘의 주요 기사 / Today\'s Top Stories</div>'
        f'{items_html}'
        f'</div>'
    )
    st.markdown(flatten_html(html), unsafe_allow_html=True)

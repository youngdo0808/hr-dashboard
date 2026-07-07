"""
services/signals.py
───────────────────────────────────────────────────────────────────────────
Dashboard 상단의 "Today's HR Signals" 메트릭 카드에 들어갈 데이터를 계산한다.
각 시그널은 키워드로 매칭된 기사 수와, 해당 기사들의 평균 감성(긍/부정 비율)으로
방향(↑/↓)을 결정한다 — 완전히 데이터 기반이며 하드코딩된 방향이 아니다.
"""
import pandas as pd

SIGNAL_DEFS = [
    {"key": "hiring", "label": "Hiring", "label_ko": "채용", "icon": "💼",
     "kw": ["채용", "구인", "인재영입", "hiring", "recruit", "talent acquisition"]},
    {"key": "ai_hr", "label": "AI HR", "label_ko": "AI 인사", "icon": "🤖",
     "kw": ["ai 채용", "hr테크", "인사 자동화", "ai hiring", "hr tech", "agentic ai", "generative ai"]},
    {"key": "payroll", "label": "Payroll", "label_ko": "급여", "icon": "💳",
     "kw": ["급여", "임금체계", "payroll", "pay transparency", "임금인상"]},
    {"key": "layoff", "label": "Layoff", "label_ko": "구조조정", "icon": "📉",
     "kw": ["구조조정", "해고", "감원", "layoff", "downsizing", "job cuts"]},
    {"key": "remote", "label": "Remote", "label_ko": "재택근무", "icon": "🏠",
     "kw": ["재택근무", "하이브리드근무", "remote work", "hybrid work", "return to office", "rto"]},
    {"key": "leadership", "label": "Leadership", "label_ko": "리더십", "icon": "🎯",
     "kw": ["리더십", "임원인사", "leadership", "executive", "manager"]},
    {"key": "learning", "label": "Learning", "label_ko": "교육·리스킬링", "icon": "📚",
     "kw": ["리스킬링", "업스킬링", "교육", "reskilling", "upskilling", "learning"]},
    {"key": "compensation", "label": "Compensation", "label_ko": "보상", "icon": "💰",
     "kw": ["연봉", "성과급", "복리후생", "compensation", "salary", "benefits", "bonus"]},
]


def _match(text: str, kws) -> bool:
    t = text.lower()
    return any(k.lower() in t for k in kws)


def compute_signals(df: pd.DataFrame) -> list:
    if df is None or df.empty:
        return []
    text_series = (df["title"].fillna("") + " " + df.get("description", "").fillna(""))
    results = []
    for sig in SIGNAL_DEFS:
        mask = text_series.apply(lambda t: _match(t, sig["kw"]))
        subset = df[mask]
        count = len(subset)
        if count == 0:
            continue
        pos = subset["sentiment"].str.contains("긍정", na=False).sum() if "sentiment" in subset else 0
        neg = subset["sentiment"].str.contains("부정", na=False).sum() if "sentiment" in subset else 0
        direction = "up" if pos >= neg else "down"
        results.append({
            "icon": sig["icon"], "count": count, "label": sig["label"], "label_ko": sig["label_ko"],
            "direction": direction, "arrow": "▲" if direction == "up" else "▼",
            "color": "#059669" if direction == "up" else "#DC2626",
        })
    results.sort(key=lambda x: x["count"], reverse=True)
    return results[:8]

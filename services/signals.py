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
    {"key": "payroll", "label": "Payroll", "label_ko": "급여·임금", "icon": "💳",
     "kw": ["급여", "임금체계", "payroll", "pay transparency", "임금인상", "통상임금", "포괄임금", "직무급", "임금피크제"]},
    {"key": "layoff", "label": "Layoff", "label_ko": "구조조정·감원", "icon": "📉",
     "kw": ["구조조정", "해고", "감원", "희망퇴직", "명예퇴직", "layoff", "downsizing", "job cuts", "voluntary separation", "early retirement"]},
    {"key": "remote", "label": "Remote", "label_ko": "재택근무", "icon": "🏠",
     "kw": ["재택근무", "하이브리드근무", "remote work", "hybrid work", "return to office", "rto"]},
    {"key": "leadership", "label": "Leadership", "label_ko": "리더십·인사", "icon": "🎯",
     "kw": ["리더십", "임원인사", "승진", "보임", "leadership development", "executive leadership", "c-suite", "management layer"]},
    {"key": "learning", "label": "Learning", "label_ko": "교육·리스킬링", "icon": "📚",
     "kw": ["리스킬링", "업스킬링", "사내교육", "직원교육", "hrd", "reskilling", "upskilling", "learning & development", "corporate training"]},
    {"key": "compensation", "label": "Compensation", "label_ko": "보상", "icon": "💰",
     "kw": ["연봉", "성과급", "복리후생", "compensation", "salary increase", "pay raise", "bonus", "total rewards"]},
    {"key": "safety", "label": "Safety", "label_ko": "산업안전", "icon": "🦺",
     "kw": ["중대재해처벌법", "산업안전보건법", "중대재해", "산재", "workplace safety", "industrial accident", "safety compliance"]},
]


def _match(text: str, kws) -> bool:
    t = text.lower()
    return any(k.lower() in t for k in kws)


def compute_signals(df: pd.DataFrame) -> list:
    if df is None or df.empty:
        return []
    desc_col = df["description"].fillna("") if "description" in df.columns else pd.Series("", index=df.index)
    text_series = df["title"].fillna("") + " " + desc_col
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
            "key": sig["key"],
            "kw": sig["kw"],
            "icon": sig["icon"], "count": count, "label": sig["label"], "label_ko": sig["label_ko"],
            "direction": direction, "arrow": "▲" if direction == "up" else "▼",
            "color": "#059669" if direction == "up" else "#DC2626",
        })
    results.sort(key=lambda x: x["count"], reverse=True)
    return results[:9]

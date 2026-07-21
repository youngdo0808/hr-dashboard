"""
services/summarizer.py
───────────────────────────────────────────────────────────────────────────
모든 뉴스 카드는 예외 없이 다음 4개 블록을 갖는다 (스펙 §8):
  Key Summary(bullets) / Business Impact / HR Insight / (Read Original은 카드에서 처리)

- Gemini API 키가 있으면 실제 기사 내용을 바탕으로 AI가 생성.
- 없거나 실패하면 규칙 기반(rule-based) 생성으로 즉시 폴백 — 절대 빈 값이나
  "..."으로 끝나는 원문 발췌를 그대로 노출하지 않는다.
"""
from __future__ import annotations

import re
import time

import streamlit as st

from utils.helpers import sentence_bullets  # re-export for backward compatibility

# ──────────────────────────────────────────────────────────────────────────
# 카테고리별 Business Impact / HR Insight / Action 규칙 기반 템플릿
# ──────────────────────────────────────────────────────────────────────────
_IMPACT_KO = {
    "채용·인재확보 / Recruiting": "채용 경쟁력과 인재 확보 속도에 직접 영향을 미쳐, 핵심 포지션의 공석 기간과 채용 비용이 달라질 수 있습니다.",
    "HR전략·조직문화 / HR Strategy": "조직 몰입도와 인재 유지율에 중장기적으로 영향을 미쳐, 이직률과 생산성 지표가 변화할 수 있습니다.",
    "벤치마킹·글로벌트렌드 / Benchmarking": "글로벌 HR 트렌드 대비 자사의 경쟁 위치를 재점검하게 하며, 중장기 HR 전략 수립에 참고 지표가 됩니다.",
    "노동법·노무 / Labor Law": "컴플라이언스 리스크와 직결되며, 미대응 시 과태료·소송 등 법적 리스크로 이어질 수 있습니다.",
    "노사·노조 / Labor Relations": "노사관계 안정성과 조직 내 신뢰에 영향을 미쳐, 단체교섭 및 내부 커뮤니케이션 전략에 시사점을 줍니다.",
}
_INSIGHT_KO = {
    "채용·인재확보 / Recruiting": "경쟁사의 채용 조건과 시장 임금 밴드를 함께 점검하고, 후보자 경험 개선 여지가 있는지 확인하세요.",
    "HR전략·조직문화 / HR Strategy": "리더십 파이프라인과 조직문화 진단 결과를 함께 검토해, 유사한 이슈가 우리 조직에도 있는지 점검하세요.",
    "벤치마킹·글로벌트렌드 / Benchmarking": "해당 트렌드가 국내 시장과 자사 산업군에도 적용 가능한지 우선순위를 매겨 검토하세요.",
    "노동법·노무 / Labor Law": "사내 취업규칙, 근로계약서, 노사협의 절차가 최신 법령을 반영하고 있는지 법무팀과 함께 확인하세요.",
    "노사·노조 / Labor Relations": "유사 이슈가 자사 노사 협의 안건에 있는지, 사전에 소통 채널을 마련해둘 필요가 있는지 점검하세요.",
}
_ACTION_KO = {
    "채용·인재확보 / Recruiting": "핵심 포지션의 채용 공고 문구와 처우 조건을 재점검하고, 소싱 채널을 다변화하세요.",
    "HR전략·조직문화 / HR Strategy": "리더 대상 설문이나 1:1 미팅을 통해 조직 내 유사 이슈가 있는지 점검하세요.",
    "벤치마킹·글로벌트렌드 / Benchmarking": "경영진 보고 자료에 해당 트렌드를 반영하고, 자사 적용 가능성에 대한 실무 검토를 시작하세요.",
    "노동법·노무 / Labor Law": "법무팀과 협업하여 관련 규정 변경사항을 사내 정책·계약서에 반영할 일정을 수립하세요.",
    "노사·노조 / Labor Relations": "노사협의회 안건으로 상정하고, 관련 부서와 사전 커뮤니케이션 계획을 수립하세요.",
}
_IMPACT_EN = {
    "채용·인재확보 / Recruiting": "Directly affects hiring competitiveness and time-to-fill for key roles, changing both vacancy duration and recruiting cost.",
    "HR전략·조직문화 / HR Strategy": "Shapes engagement and retention over the medium term, likely shifting turnover and productivity metrics.",
    "벤치마킹·글로벌트렌드 / Benchmarking": "Prompts a re-check of your organization's competitive position against global HR trends.",
    "노동법·노무 / Labor Law": "Carries direct compliance risk; failure to act could lead to fines or litigation exposure.",
    "노사·노조 / Labor Relations": "Affects labor-relations stability and internal trust, with implications for collective bargaining strategy.",
}
_INSIGHT_EN = {
    "채용·인재확보 / Recruiting": "Benchmark competitor offers and market pay bands, and check whether candidate experience needs improvement.",
    "HR전략·조직문화 / HR Strategy": "Review your leadership pipeline and culture survey data to see if similar issues exist internally.",
    "벤치마킹·글로벌트렌드 / Benchmarking": "Assess whether this trend applies to the Korean market and your industry, and prioritize accordingly.",
    "노동법·노무 / Labor Law": "Confirm with legal that employment contracts and internal policy reflect the latest regulations.",
    "노사·노조 / Labor Relations": "Check whether similar issues are on your labor-management agenda and prepare communication channels in advance.",
}
_ACTION_EN = {
    "채용·인재확보 / Recruiting": "Re-check job postings and offer terms for key roles, and diversify sourcing channels.",
    "HR전략·조직문화 / HR Strategy": "Run leader surveys or 1:1s to check for similar issues inside your organization.",
    "벤치마킹·글로벌트렌드 / Benchmarking": "Reflect the trend in leadership reporting and start a feasibility review for your organization.",
    "노동법·노무 / Labor Law": "Work with legal to schedule updates to contracts and internal policy documents.",
    "노사·노조 / Labor Relations": "Put it on the labor-management council agenda and plan stakeholder communication in advance.",
}
_DEFAULT = {
    "impact_ko": "인사담당자는 이 이슈가 우리 조직의 채용·보상·문화 정책에 미칠 영향을 함께 점검해볼 필요가 있습니다.",
    "insight_ko": "관련 부서와 공유하여 자사 정책 대비 시사점을 논의해보세요.",
    "action_ko": "필요 시 팀 내에서 후속 논의를 진행하세요.",
    "impact_en": "HR leaders should assess how this development could affect hiring, pay, or culture policy internally.",
    "insight_en": "Share with relevant stakeholders and discuss implications versus current internal policy.",
    "action_en": "Schedule a follow-up discussion within your team if relevant.",
}


def _short_title(title: str, max_len: int = 50) -> str:
    """기사 제목에서 핵심 구문만 추출한다 (콜론 이전, 최대 max_len자)."""
    core = title.split(":")[0].split("—")[0].split("–")[0].strip()
    if len(core) <= max_len:
        return core
    return core[:max_len].rsplit(" ", 1)[0]


def rule_based_structured(title: str, description: str, category: str) -> dict:
    """API 키 없이도 항상 완전한 4-블록 구조를 만든다.
    Business Impact는 기사 제목을 반영해 카드마다 다르게 표시한다."""
    ko_points = sentence_bullets(description, max_bullets=3)
    if not ko_points:
        ko_points = [f"『{title}』 관련 소식입니다." if _is_korean(title) else f'Related update: "{title}".']

    desc_is_korean = _is_korean(description)
    title_is_korean = _is_korean(title)
    if desc_is_korean or (not description.strip() and title_is_korean):
        clean_title = title.rstrip(".")
        en_points = [
            f"Key update: {clean_title}.",
            "For full details, please refer to the original article.",
        ]
    else:
        en_points = ko_points

    # ── Article-specific Business Impact ──────────────────────────────────
    # 기사 제목을 삽입해 모든 카드가 다른 비즈니스 영향을 표시하도록 한다.
    base_impact_ko = _IMPACT_KO.get(category, _DEFAULT["impact_ko"])
    base_impact_en = _IMPACT_EN.get(category, _DEFAULT["impact_en"])
    s = _short_title(title)

    if title_is_korean:
        impact_ko = f"「{s}」 관련 동향은 {base_impact_ko}"
        impact_en = base_impact_en  # 영문 제목 없으면 영문 템플릿 그대로
    else:
        impact_ko = f"이번 '{s}' 관련 이슈는 {base_impact_ko}"
        # 영문 첫 글자 소문자로 자연스럽게 연결
        rest_en = base_impact_en[0].lower() + base_impact_en[1:] if base_impact_en else ""
        impact_en = f'The "{s}" development {rest_en}'

    return {
        "ko": {
            "points": ko_points,
            "impact": impact_ko,
            "insight": _INSIGHT_KO.get(category, _DEFAULT["insight_ko"]),
            "action": _ACTION_KO.get(category, _DEFAULT["action_ko"]),
        },
        "en": {
            "points": en_points,
            "impact": impact_en,
            "insight": _INSIGHT_EN.get(category, _DEFAULT["insight_en"]),
            "action": _ACTION_EN.get(category, _DEFAULT["action_en"]),
        },
    }


def _is_korean(text: str) -> bool:
    return bool(re.search(r"[가-힣]", text or ""))


# ──────────────────────────────────────────────────────────────────────────
# Gemini AI
# ──────────────────────────────────────────────────────────────────────────
def get_gemini_client():
    try:
        from google import genai
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if not api_key or api_key == "여기에_입력":
            return None
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def _build_prompt(title, description, category, lang="ko"):
    if lang == "ko":
        return f"""당신은 HR 전문 애널리스트입니다. 아래 뉴스를 분석해 HR 담당자에게 실용적인 정보를 주세요.
이 기사가 HR, 인력, 비즈니스 전략, 노동, 조직문화와 무관하다면 'NOT_HR_RELEVANT'만 응답하세요.

카테고리: {category}
제목: {title}
내용: {description}

반드시 아래 형식 그대로만 답변하세요. 다른 문장이나 설명은 절대 추가하지 마세요.
각 항목은 완전한 문장으로, 절대 중간에 끊기지 않게 작성하세요.

POINT: [핵심 사실 1 - 완전한 문장]
POINT: [핵심 사실 2 - 완전한 문장]
POINT: [핵심 사실 3 - 완전한 문장]
IMPACT: [기업 입장에서의 비즈니스 영향 - 완전한 문장]
INSIGHT: [HR 담당자가 고려해야 할 시사점 - 완전한 문장]
ACTION: [지금 취할 수 있는 실무 조치 - 완전한 문장]"""
    return f"""You are a professional HR analyst. Analyze the news below for HR professionals.
If this article is not relevant to HR, workforce, business strategy, labor, or organizational culture, respond only with: NOT_HR_RELEVANT

Category: {category}
Title: {title}
Content: {description}

Reply ONLY in the exact format below. No extra text. Each line must be one complete sentence, never cut off mid-sentence.

POINT: [Key fact 1 - complete sentence]
POINT: [Key fact 2 - complete sentence]
POINT: [Key fact 3 - complete sentence]
IMPACT: [Business impact for the company - complete sentence]
INSIGHT: [What HR leaders should consider - complete sentence]
ACTION: [An immediate actionable step - complete sentence]"""


_END_PUNCT = (".", "!", "?", "다", "다.", "요", "요.", ")", "」", "』", '"')


def _is_complete(s: str) -> bool:
    """문장이 온전히 끝났는지 검사 — 중간에 끊긴 응답은 폐기하고 규칙 기반으로 대체한다."""
    s = s.strip()
    if not s:
        return False
    return s.endswith(_END_PUNCT)


def _parse_structured(text: str) -> dict:
    if "NOT_HR_RELEVANT" in (text or "").upper():
        return {"points": [], "impact": "", "insight": "", "action": ""}
    points, impact, insight, action = [], "", "", ""
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("POINT:"):
            points.append(line.split(":", 1)[1].strip())
        elif line.upper().startswith("IMPACT:"):
            impact = line.split(":", 1)[1].strip()
        elif line.upper().startswith("INSIGHT:"):
            insight = line.split(":", 1)[1].strip()
        elif line.upper().startswith("ACTION:"):
            action = line.split(":", 1)[1].strip()
    if not any([points, impact, insight, action]):
        sentences = [s.strip() for s in re.split(r"(?<=[.!?다요])\s+", text) if s.strip()]
        points = sentences[:3] if sentences else [text.strip()]
    # 중간에 끊긴 문장(마지막 POINT 등)은 통째로 버려서 잘린 채로 노출되지 않게 한다
    points = [p for p in points if _is_complete(p)]
    if impact and not _is_complete(impact):
        impact = ""
    if insight and not _is_complete(insight):
        insight = ""
    if action and not _is_complete(action):
        action = ""
    return {"points": points, "impact": impact, "insight": insight, "action": action}


@st.cache_data(ttl=86400, show_spinner=False)
def _ai_structured(title: str, description: str, category: str) -> dict | None:
    client = get_gemini_client()
    if not client:
        return None
    # description이 너무 짧으면 title을 description으로 보완해 Gemini가 분석할 수 있게 한다
    effective_desc = description.strip() if len(description.strip()) >= 20 else title.strip()
    if not effective_desc:
        return None
    from google.genai import types
    out = {}
    for lang in ("ko", "en"):
        prompt = _build_prompt(title, effective_desc, category, lang)
        parsed = None
        for attempt in range(2):
            try:
                resp = client.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=2048,
                        temperature=0.3,
                        thinking_config=types.ThinkingConfig(thinking_budget=0),
                    ),
                )
                parsed = _parse_structured((resp.text or "").strip())
                time.sleep(0.3)
                break
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    time.sleep(1.5 ** attempt)
                    continue
                return None
        if not parsed or not any(parsed.values()):
            return None
        out[lang] = parsed
    return out or None


def get_structured_summary(title: str, description: str, category: str, ai_on: bool) -> dict:
    """항상 {'ko': {...}, 'en': {...}} 형태의 완전한 4-블록 구조를 반환한다."""
    fallback = rule_based_structured(title, description, category)
    if not ai_on:
        return fallback
    ai_result = _ai_structured(title, description, category)
    if not ai_result:
        return fallback
    for lang in ("ko", "en"):
        for key in ("points", "impact", "insight", "action"):
            if not ai_result.get(lang, {}).get(key):
                ai_result.setdefault(lang, {})[key] = fallback[lang][key]
    return ai_result

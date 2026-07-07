import requests
import feedparser
import pandas as pd
import streamlit as st
from datetime import datetime
import re

SOURCE_TRUST = {
    "고용노동부":   {"grade": "공식기관 / Official", "color": "#6D28D9"},
    "ILO":          {"grade": "공식기관 / Official", "color": "#6D28D9"},
    "OECD":         {"grade": "공식기관 / Official", "color": "#6D28D9"},
    "WEF":          {"grade": "공식기관 / Official", "color": "#6D28D9"},
    "McKinsey":     {"grade": "싱크탱크 / Think Tank", "color": "#0369A1"},
    "Korn Ferry":   {"grade": "싱크탱크 / Think Tank", "color": "#0369A1"},
    "Bloomberg":    {"grade": "글로벌 미디어 / Global Media", "color": "#B45309"},
    "Deloitte":     {"grade": "싱크탱크 / Think Tank", "color": "#0369A1"},
    "BCG":          {"grade": "싱크탱크 / Think Tank", "color": "#0369A1"},
    "SHRM":         {"grade": "전문매체 / Specialist", "color": "#0F766E"},
    "HR Dive":      {"grade": "전문매체 / Specialist", "color": "#0F766E"},
    "HR Executive": {"grade": "전문매체 / Specialist", "color": "#0F766E"},
    "HR Morning":   {"grade": "전문매체 / Specialist", "color": "#0F766E"},
    "HR Gazette":   {"grade": "전문매체 / Specialist", "color": "#0F766E"},
    "HR Grapevine": {"grade": "전문매체 / Specialist", "color": "#0F766E"},
    "HR Exchange":  {"grade": "전문매체 / Specialist", "color": "#0F766E"},
    "HR Tech Feed": {"grade": "전문매체 / Specialist", "color": "#0F766E"},
    "HR Daily":     {"grade": "APAC 전문 / APAC", "color": "#0891B2"},
    "HR Katha":     {"grade": "APAC 전문 / APAC", "color": "#0891B2"},
    "Korea Herald": {"grade": "APAC 전문 / APAC", "color": "#0891B2"},
    "매일노동뉴스": {"grade": "국내 전문 / Domestic", "color": "#047857"},
    "ZDNet":        {"grade": "국내 전문 / Domestic", "color": "#047857"},
    "JoongAng":     {"grade": "국내 전문 / Domestic", "color": "#047857"},
    "Reuters":      {"grade": "글로벌 미디어 / Global Media", "color": "#B45309"},
    "CNBC":         {"grade": "글로벌 미디어 / Global Media", "color": "#B45309"},
    "BBC":          {"grade": "글로벌 미디어 / Global Media", "color": "#B45309"},
    "HBR":          {"grade": "싱크탱크 / Think Tank", "color": "#0369A1"},
    "Fortune":      {"grade": "글로벌 미디어 / Global Media", "color": "#B45309"},
    "Nikkei":       {"grade": "APAC 전문 / APAC", "color": "#0891B2"},
    "Naver":        {"grade": "뉴스 집계 / Aggregator", "color": "#64748B"},
    "NewsData":     {"grade": "뉴스 집계 / Aggregator", "color": "#64748B"},
}


def get_trust(source_name):
    for key, val in SOURCE_TRUST.items():
        if key.lower() in str(source_name).lower():
            return val
    return {"grade": "뉴스 집계 / Aggregator", "color": "#64748B"}


def clean_html(text):
    text = re.sub(r"<[^>]+>", "", str(text or ""))
    for h, r in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&quot;", '"'), ("&#39;", "'"), ("&nbsp;", " ")]:
        text = text.replace(h, r)
    return text.strip()


CATEGORY_CONFIG = {
    "채용·인재확보 / Recruiting": {
        "naver_kw": ["기업 채용 트렌드", "AI 채용 면접", "인재 확보 전략", "수시채용 공채"],
        "news_kw": "recruitment hiring talent acquisition skills-based",
        "rss_keys": ["HR Dive", "HR Morning", "SHRM", "HR Executive", "HR Gazette", "HR Tech Feed", "Fortune", "HBR"],
        "color": "#2563EB", "bg": "#EFF6FF", "icon": "💼",
        "desc_ko": "채용 트렌드 · AI 면접 · 글로벌 인재 시장",
        "desc_en": "Hiring Trends · AI Interviews · Global Talent Market",
    },
    "HR전략·조직문화 / HR Strategy": {
        "naver_kw": ["기업 조직문화", "직원 경험 HR", "인사 혁신 전략", "HR 리더십"],
        "news_kw": "HR strategy employee experience culture engagement retention",
        "rss_keys": ["HR Dive", "SHRM", "HR Morning", "HR Executive", "HR Gazette", "HR Exchange Talent", "HBR", "CNBC Work"],
        "color": "#7C3AED", "bg": "#F5F3FF", "icon": "🧭",
        "desc_ko": "HR 전략 · 조직문화 · EX 설계",
        "desc_en": "HR Strategy · Culture · Employee Experience",
    },
    "벤치마킹·글로벌트렌드 / Benchmarking": {
        "naver_kw": ["글로벌 인사 트렌드", "미래 인재 전략", "AI 시대 HR"],
        "news_kw": "future of work workforce transformation AI automation HR innovation",
        "rss_keys": ["SHRM", "HR Morning", "ILO", "WEF", "HR Tech Feed", "HR Executive", "HR Katha", "HR Daily", "Reuters Biz", "Nikkei Asia", "HBR"],
        "color": "#D97706", "bg": "#FFFBEB", "icon": "🌍",
        "desc_ko": "WEF·McKinsey·Korn Ferry 글로벌 트렌드",
        "desc_en": "WEF · McKinsey · Korn Ferry Global Trends",
    },
    "노동법·노무 / Labor Law": {
        "naver_kw": ["근로기준법 개정", "최저임금 노동부", "인사노무 컴플라이언스"],
        "news_kw": "labor law employment regulation minimum wage compliance pay transparency",
        "rss_keys": ["고용노동부 공식", "고용노동부 정책", "Korea Herald", "Korea JoongAng", "ILO", "OECD", "SHRM", "HR Exchange Labor", "Reuters Biz"],
        "color": "#DC2626", "bg": "#FEF2F2", "icon": "⚖️",
        "desc_ko": "국내외 노동법 · 임금 · 글로벌 규제",
        "desc_en": "Labor Law · Wages · Global Compliance",
    },
    "노사·노조 / Labor Relations": {
        "naver_kw": ["기업 노사관계", "노조 단체협약", "정년연장 임금체계"],
        "news_kw": "union labor relations strike collective bargaining gig workers",
        "rss_keys": ["매일노동뉴스", "고용노동부 공식", "ILO", "HR Grapevine", "HR Dive", "HR Exchange Labor", "BBC Work", "ZDNet Korea"],
        "color": "#059669", "bg": "#ECFDF5", "icon": "🤝",
        "desc_ko": "노조 동향 · 노사 협상 · 글로벌 파업",
        "desc_en": "Union Trends · Negotiations · Global Strikes",
    },
}

# 관련 없는 뉴스(스포츠·정치·운세 등)를 걸러내기 위한 필터
HR_RELEVANCE_KW = [
    "hr전략", "hr트렌드", "hr팀", "hr담당", "인사팀", "인사담당", "인사정책",
    "인사이동", "인사관리", "인사혁신", "인사노무", "채용", "노무", "노동법",
    "노동조합", "근로기준법", "근로자", "임금협상", "인재확보", "인재육성",
    "조직문화", "직원경험", "직원복지", "복리후생", "이직률", "퇴직연금",
    "고용시장", "연봉협상", "워라밸", "재택근무", "하이브리드근무",
    "육아휴직", "정년연장", "임원인사", "구인난", "구직자", "취업준비",
    "채용면접", "온보딩", "리스킬링", "업스킬링", "번아웃", "직장내괴롭힘",
    "recruit", "hiring", "talent management", "talent acquisition", "workforce",
    "employee experience", "workplace culture", "reskilling", "upskilling", "retention",
    "hr compliance", "labor law", "employment law", "labor policy", "labor market",
    "minimum wage", "pay transparency", "pay equity", "compensation", "salary increase",
    "employee benefits", "collective bargaining", "union strike", "labor union",
    "layoffs", "job cuts", "workforce reduction", "return to office", "hybrid work",
    "remote work", "four-day workweek", "parental leave", "succession planning",
    "performance management", "employer branding", "candidate experience", "skills gap",
    "hr tech", "people analytics", "generative ai workforce", "agentic ai hr",
    "future of work", "employee engagement", "employee turnover", "attrition",
    "gig workers", "quiet quitting", "burnout", "workplace harassment", "dei",
    "diversity equity inclusion", "leadership development", "hr strategy",
    "chro", "human capital", "job market", "unemployment rate",
]
EXCLUDE_KW = [
    "축구", "야구", "농구", "배구", "골프", "올림픽", "월드컵", "국가대표",
    "감독", "선수", "리그", "챔피언스", "구단", "경기 결과", "홈런", "득점",
    "이적", "드래프트", "16강", "8강", "4강", "결승", "금메달", "은메달", "동메달",
    "손흥민", "박지성", "이강인", "황희찬", "김민재", "황선홍", "홍명보",
    "대통령", "국회", "여야", "정당", "대선", "총선", "검찰", "기소", "탄핵",
    "의원", "도지사", "국정감사", "여의도 정치", "지방선거", "공천",
    "오늘의 운세", "운세", "사주", "별자리", "타로", "궁합",
    "football", "soccer", "world cup", "olympics", "box office", "k-pop",
]


def is_hr_relevant(title, description):
    title_l = title.lower().replace(" ", "")
    text = f"{title} {description}".lower().replace(" ", "")
    if any(bad.lower().replace(" ", "") in text for bad in EXCLUDE_KW):
        return False
    # 제목에 HR 키워드가 있으면 확실히 통과
    if any(kw.lower().replace(" ", "") in title_l for kw in HR_RELEVANCE_KW):
        return True
    # 제목엔 없지만 본문에 있는 경우, 최소 2개 이상 매칭되어야 통과 (우연히 한 단어만 겹치는 오탐 방지)
    hits = sum(1 for kw in HR_RELEVANCE_KW if kw.lower().replace(" ", "") in text)
    return hits >= 2


RSS_SOURCES = {
    "고용노동부 공식":    ("https://www.moel.go.kr/rss/notice.do", "국내"),
    "고용노동부 정책":    ("https://www.moel.go.kr/rss/policy.do", "국내"),
    "매일노동뉴스":       ("https://www.labortoday.co.kr/rss/allArticle.xml", "국내"),
    "Korea Herald":       ("http://www.koreaherald.com/rss/social.xml", "국내(영)"),
    "ILO":                ("https://www.ilo.org/global/about-the-ilo/newsroom/rss/lang--en/index.htm", "글로벌"),
    "OECD":               ("https://www.oecd.org/feed/topicen/employment/news.xml", "글로벌"),
    "WEF":                ("https://www.weforum.org/rss-feeds/work/", "글로벌"),
    # 참고: SHRM은 신규 웹사이트 전환 후 공식적으로 RSS 미지원 상태입니다
    # (SHRM 자체 고지: "the new SHRM website does not support RSS feeds").
    # 아래는 제거했으며, CATEGORY_CONFIG의 rss_keys에 "SHRM"이 남아있어도
    # fetch_rss 루프가 안전하게 건너뜁니다.
    "HR Dive":            ("https://www.hrdive.com/feeds/news/", "글로벌"),
    "HR Executive":       ("https://hrexecutive.com/feed/", "글로벌"),
    "HR Morning":         ("https://www.hrmorning.com/feed/", "글로벌"),
    "HR Gazette":         ("https://hr-gazette.com/feed/", "글로벌"),
    "HR Tech Feed":       ("https://hrtechfeed.com/feed/", "글로벌"),
    "HR Grapevine":       ("https://www.hrgrapevine.com/rss", "글로벌(EU)"),
    "HR Exchange Labor":  ("https://www.hrexchangenetwork.com/rss/employment-law", "글로벌"),
    "HR Exchange Talent": ("https://www.hrexchangenetwork.com/rss/talent-management", "글로벌"),
    "HR Daily":           ("https://www.hrdaily.com.au/rss", "APAC"),
    "HR Katha":           ("https://www.hrkatha.com/feed/", "APAC"),
    "Bloomberg Econ":     ("https://feeds.bloomberg.com/economics/news.rss", "글로벌"),
    "Bloomberg Biz":      ("https://feeds.bloomberg.com/industries/news.rss", "글로벌"),
    "McKinsey":           ("https://www.mckinsey.com/insights/rss", "글로벌"),
    "Reuters Biz":        ("https://feeds.reuters.com/reuters/businessNews", "글로벌"),
    "CNBC Work":          ("https://search.cnbc.com/rs/search/combinedcombined.xml?partnerId=wrss01&id=10000108", "글로벌"),
    "BBC Work":           ("https://feeds.bbci.co.uk/news/business/rss.xml", "글로벌"),
    "HBR":                ("https://feeds.hbr.org/harvardbusiness", "글로벌"),
    "Fortune":            ("https://fortune.com/feed/", "글로벌"),
    "ZDNet Korea":        ("https://www.zdnet.co.kr/rss/rss.php", "국내"),
    "Korea JoongAng":     ("https://koreajoongangdaily.joins.com/rss/rss.xml", "국내(영)"),
    "Nikkei Asia":        ("https://asia.nikkei.com/rss/feed/nar", "APAC"),
}

CURATED_INSIGHTS = [
    {
        "title": "HR Monitor 2025: Strategic vs. Operational HR Gap Widens",
        "title_ko": "HR Monitor 2025: 전략적 HR과 운영 HR의 격차 확대",
        "summary_ko": "McKinsey 조사에 따르면 73%의 기업이 운영 계획을 수행하지만, 3년 이상의 전략적 인력 계획을 수립하는 HR 리더는 12%에 불과합니다.",
        "summary_en": "McKinsey found that while 73% of organizations conduct operational planning, only 12% of HR leaders perform strategic workforce planning with a 3+ year horizon.",
        "insight_ko": "단기 채용·운영 중심에서 벗어나 중장기 인력 포트폴리오 설계를 HR 의제의 최우선 순위로 올려야 합니다.",
        "insight_en": "HR must shift from short-term operational tasks to designing long-term workforce portfolios as the top strategic priority.",
        "action_ko": "연간 인력계획 주기를 3년 이상으로 확장하고 CHRO를 경영전략 회의에 정식 참여시키세요.",
        "action_en": "Extend your workforce planning cycle to 3+ years and formally include the CHRO in all strategic management meetings.",
        "source": "McKinsey & Company",
        "url": "https://www.mckinsey.com/capabilities/people-and-organizational-performance/our-insights/hr-monitor-2025",
        "category": "벤치마킹·글로벌트렌드 / Benchmarking",
        "region": "글로벌", "published_str": "2025-01", "tag": "McKinsey Report",
    },
    {
        "title": "Agentic AI: 70% of HR Tasks to Be Automated",
        "title_ko": "Agentic AI 시대: HR 업무의 70%가 AI 에이전트로 전환",
        "summary_ko": "McKinsey State of AI 2025에 따르면 서류 검토·온보딩·직원 Q&A 등 반복 HR 업무의 70%가 Agentic AI로 대체될 전망입니다.",
        "summary_en": "McKinsey's State of AI 2025 projects that 70% of repetitive HR tasks will be handled by Agentic AI.",
        "insight_ko": "HR 담당자의 역할이 '관리자'에서 'AI 협업 설계자'로 전환됩니다.",
        "insight_en": "The HR role is shifting from 'administrator' to 'AI collaboration designer.'",
        "action_ko": "HR 팀 내 AI 리터러시 교육 로드맵을 수립하고 파일럿 자동화 프로세스 3개를 선정해 도입하세요.",
        "action_en": "Build an AI literacy roadmap for your HR team and identify 3 pilot automation processes.",
        "source": "McKinsey & Company",
        "url": "https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai",
        "category": "HR전략·조직문화 / HR Strategy",
        "region": "글로벌", "published_str": "2025-03", "tag": "McKinsey Report",
    },
    {
        "title": "Skills Gap Crisis: 32% of Employees Lack Required Competencies",
        "title_ko": "스킬 격차 위기: 직원 32%가 현재 직무에 필요한 역량 부족",
        "summary_ko": "McKinsey 분석 결과 전체 직원의 32%가 현재 담당 직무 수행에 필요한 핵심 스킬이 부족한 것으로 나타났습니다.",
        "summary_en": "McKinsey analysis reveals that 32% of all employees lack the critical skills needed for their current roles.",
        "insight_ko": "채용보다 리스킬링이 더 빠르고 저렴한 해결책입니다.",
        "insight_en": "Reskilling is faster and more cost-effective than external hiring.",
        "action_ko": "전사 스킬 갭 분석을 실시하고 직무별 핵심 스킬 맵을 올해 안에 완성하세요.",
        "action_en": "Conduct a company-wide skills gap analysis and complete a role-based critical skills map.",
        "source": "McKinsey & Company",
        "url": "https://www.mckinsey.com/featured-insights/future-of-work",
        "category": "채용·인재확보 / Recruiting",
        "region": "글로벌", "published_str": "2025-02", "tag": "McKinsey Report",
    },
    {
        "title": "Workforce 2025: The 'Missing Manager' Crisis After 41% Layer Cuts",
        "title_ko": "Workforce 2025: 관리자 41% 감축 후 '미싱 매니저' 위기",
        "summary_ko": "Korn Ferry 글로벌 조사에서 41%의 조직이 관리 계층을 대폭 축소했고, 중간관리자 부재로 인한 팀 성과 저하와 번아웃이 급증하고 있습니다.",
        "summary_en": "Korn Ferry's global survey shows 41% of organizations have drastically cut management layers.",
        "insight_ko": "구조 조정 후 살아남은 관리자들의 관리 범위가 과도하게 확장됩니다.",
        "insight_en": "Surviving managers now face overextended spans of control.",
        "action_ko": "팀장급 대상 코칭 프로그램을 즉시 도입하고 관리자 1인당 적정 직속 보고 인원(7명 이하)을 기준으로 재조직화하세요.",
        "action_en": "Launch a coaching program for team leaders and reorganize based on optimal direct report ratio.",
        "source": "Korn Ferry",
        "url": "https://www.kornferry.com/insights/featured-topics/workforce-management-articles/workforce-planning-insights",
        "category": "HR전략·조직문화 / HR Strategy",
        "region": "글로벌", "published_str": "2025-02", "tag": "Korn Ferry Report",
    },
    {
        "title": "EVP Evolved: 67% Stay at Jobs They Dislike for Growth Opportunities",
        "title_ko": "EVP의 진화: 직원 67%는 성장 기회가 있다면 불만족 직장도 유지",
        "summary_ko": "Korn Ferry 2025 CHRO Survey에 따르면 직원 67%가 리스킬링·업스킬링 기회가 있으면 현 직장을 유지하겠다고 응답했습니다.",
        "summary_en": "Korn Ferry's 2025 CHRO Survey shows 67% of employees would stay if offered reskilling opportunities.",
        "insight_ko": "연봉 인상보다 '성장 스토리'가 핵심 리텐션 도구입니다.",
        "insight_en": "A compelling 'growth narrative' outperforms salary raises as a retention tool.",
        "action_ko": "개인별 커리어 패스와 학습 예산(러닝 스티펜드) 제도를 복리후생 패키지에 포함시키세요.",
        "action_en": "Add individual career paths and a learning stipend to your benefits package.",
        "source": "Korn Ferry",
        "url": "https://www.kornferry.com/insights/this-week-in-leadership",
        "category": "HR전략·조직문화 / HR Strategy",
        "region": "글로벌", "published_str": "2025-03", "tag": "Korn Ferry Report",
    },
    {
        "title": "AI Reality Check: 70% Culture/Reskilling, 10% Tools",
        "title_ko": "AI 현실 점검: 도구 10%, 문화·리스킬링 70%에 투자해야",
        "summary_ko": "Korn Ferry는 70/20/10 AI 전환 원칙을 제시합니다. 성공의 70%는 문화·사람, 20%는 프로세스, 10%만이 기술 도구에 달려 있습니다.",
        "summary_en": "Korn Ferry proposes the 70/20/10 AI transformation principle.",
        "insight_ko": "AI 도입 실패의 90%는 기술이 아닌 사람과 문화 문제입니다.",
        "insight_en": "90% of AI adoption failures are people and culture problems, not technology.",
        "action_ko": "AI 전환 계획에 변화관리(Change Management) 예산을 기술 예산의 7배로 편성하세요.",
        "action_en": "Allocate a change management budget 7x the size of your technology budget.",
        "source": "Korn Ferry",
        "url": "https://www.kornferry.com/insights/briefings-magazine",
        "category": "벤치마킹·글로벌트렌드 / Benchmarking",
        "region": "글로벌", "published_str": "2025-04", "tag": "Korn Ferry Report",
    },
    {
        "title": "Pay Transparency Laws: 60%+ of US/EU Companies Unprepared",
        "title_ko": "임금 투명성 법안 확산: 미국·EU 기업 60% 이상 대응 준비 미흡",
        "summary_ko": "Bloomberg Law에 따르면 2025년 미국 18개 주와 EU 전체에서 임금 공시 의무화가 시행되지만, 60% 이상의 기업이 충분한 대비를 갖추지 못한 상태입니다.",
        "summary_en": "Bloomberg Law reports pay disclosure mandates took effect in 18 U.S. states and across the EU in 2025.",
        "insight_ko": "임금 투명성은 규제 리스크를 넘어 인재 유치·리텐션의 핵심 변수입니다.",
        "insight_en": "Pay transparency is now a key variable in talent attraction and retention.",
        "action_ko": "직무등급별 임금 밴드를 정비하고 채용 공고에 급여 범위를 명시하는 정책을 수립하세요.",
        "action_en": "Establish pay bands by job grade and include salary ranges in job postings.",
        "source": "Bloomberg Law",
        "url": "https://pro.bloomberglaw.com/insights/labor-employment/",
        "category": "노동법·노무 / Labor Law",
        "region": "글로벌", "published_str": "2025-01", "tag": "Bloomberg Report",
    },
    {
        "title": "RTO Mandates vs. Hybrid: Forced Return Firms See 19% Higher Turnover",
        "title_ko": "RTO 강제 vs 하이브리드: 전면 복귀 기업 이직률 19% 더 높아",
        "summary_ko": "Bloomberg Work Shift 분석에서 전면 사무실 복귀를 강제한 기업의 이직률이 하이브리드 유지 기업보다 평균 19% 높게 나타났습니다.",
        "summary_en": "Bloomberg Work Shift analysis shows companies forcing full RTO have 19% higher turnover on average.",
        "insight_ko": "RTO 강제는 단기 비용 절감처럼 보이지만 핵심 인재 이탈로 인한 채용 비용이 더 클 수 있습니다.",
        "insight_en": "Forced RTO may appear cost-saving short-term, but losing key talent may cost more.",
        "action_ko": "하이브리드 정책 변경 전 팀별 생산성 지표와 이직 의향 데이터를 먼저 수집·분석하세요.",
        "action_en": "Before changing hybrid policy, collect and analyze team-level productivity and turnover data.",
        "source": "Bloomberg",
        "url": "https://www.bloomberg.com/work-shift",
        "category": "HR전략·조직문화 / HR Strategy",
        "region": "글로벌", "published_str": "2025-02", "tag": "Bloomberg Report",
    },
    {
        "title": "Deloitte 2025 Global Human Capital Trends: Human+AI Collaboration Design",
        "title_ko": "Deloitte 2025: 인간+AI 협업 설계가 HR의 핵심 과제",
        "summary_ko": "Deloitte의 연간 인적자본 보고서는 AI와 인간의 협업 방식을 설계하는 것이 2025년 HR의 가장 중요한 과제라고 밝혔습니다.",
        "summary_en": "Deloitte's annual human capital report identifies designing Human+AI collaboration as the top HR challenge.",
        "insight_ko": "AI가 무엇을 할 수 있는가보다 사람이 AI와 함께 무엇을 해야 하는가를 정의하는 것이 HR의 새로운 역할입니다.",
        "insight_en": "HR's new role is defining what humans should do alongside AI.",
        "action_ko": "각 직무별 'Human+AI 역할 분담 매트릭스'를 작성하고 이를 직무기술서(JD)에 반영하세요.",
        "action_en": "Create a Human+AI role allocation matrix for each job function.",
        "source": "Deloitte",
        "url": "https://www2.deloitte.com/us/en/insights/focus/human-capital-trends.html",
        "category": "벤치마킹·글로벌트렌드 / Benchmarking",
        "region": "글로벌", "published_str": "2025-03", "tag": "Deloitte Report",
    },
    {
        "title": "BCG: Skills-Based Organizations Show 25% Higher Productivity",
        "title_ko": "BCG: 스킬 기반 조직 전환 기업, 생산성 25% 높아",
        "summary_ko": "BCG 연구에 따르면 직무 타이틀이 아닌 스킬 중심으로 인력을 배치하는 기업은 생산성이 평균 25% 높고 이직률은 18% 낮습니다.",
        "summary_en": "BCG research shows companies deploying talent based on skills achieve 25% higher productivity.",
        "insight_ko": "조직 설계의 기본 단위를 '직무'에서 '스킬'로 바꾸는 것이 차세대 HR 아키텍처의 핵심입니다.",
        "insight_en": "Shifting the fundamental unit of organizational design from 'job' to 'skill' is key.",
        "action_ko": "HR 시스템에 스킬 태그 체계를 도입하고 내부 인재 마켓플레이스 구축을 검토하세요.",
        "action_en": "Introduce a skill-tagging system and explore building an Internal Talent Marketplace.",
        "source": "BCG",
        "url": "https://www.bcg.com/capabilities/people-strategy/overview",
        "category": "채용·인재확보 / Recruiting",
        "region": "글로벌", "published_str": "2025-02", "tag": "BCG Report",
    },
]


def fetch_naver(keyword, display=15):
    cid = st.secrets.get("NAVER_CLIENT_ID", "")
    csec = st.secrets.get("NAVER_CLIENT_SECRET", "")
    if not cid or cid == "여기에_입력":
        return []
    headers = {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": csec}
    params = {"query": keyword, "display": display, "sort": "date"}
    try:
        r = requests.get("https://openapi.naver.com/v1/search/news.json",
                          headers=headers, params=params, timeout=8)
        result = []
        for item in r.json().get("items", []):
            result.append({
                "title": clean_html(item.get("title", "")),
                "title_ko": clean_html(item.get("title", "")),
                "description": clean_html(item.get("description", "")),
                "summary_ko": clean_html(item.get("description", "")),
                "summary_en": "",
                "insight_ko": "", "insight_en": "",
                "action_ko": "", "action_en": "",
                "url": item.get("originallink") or item.get("link", "#"),
                "source": "Naver 뉴스",
                "published": item.get("pubDate", "")[:16],
                "region": "국내",
                "trust": get_trust("Naver"),
                "tag": "",
            })
        return result
    except Exception:
        return []


def fetch_rss(source_name, rss_url, region, max_items=12):
    try:
        feed = feedparser.parse(rss_url)
        items = []
        for entry in feed.entries[:max_items]:
            pub = ""
            for attr in ["published", "updated"]:
                if hasattr(entry, attr):
                    try:
                        from dateutil import parser as dp
                        pub = dp.parse(getattr(entry, attr)).strftime("%Y-%m-%d %H:%M")
                        break
                    except Exception:
                        pub = str(getattr(entry, attr))[:16]
            desc = clean_html(
                entry.get("summary") or
                (entry.get("content") or [{}])[0].get("value", "") or
                entry.get("description", "")
            )[:500]
            if not entry.get("title"):
                continue
            t = clean_html(entry.get("title", ""))
            items.append({
                "title": t,
                "title_ko": t,
                "description": desc,
                "summary_ko": desc,
                "summary_en": "",
                "insight_ko": "", "insight_en": "",
                "action_ko": "", "action_en": "",
                "url": entry.get("link", "#"),
                "source": source_name,
                "published": pub,
                "region": region,
                "trust": get_trust(source_name),
                "tag": "",
            })
        return items
    except Exception:
        return []


def fetch_newsdata(keyword, language="en", max_items=10):
    key = st.secrets.get("NEWSDATA_API_KEY", "")
    if not key or key == "여기에_입력":
        return []
    try:
        r = requests.get(
            "https://newsdata.io/api/1/news",
            params={"apikey": key, "q": keyword, "language": language, "category": "business"},
            timeout=10
        )
        result = []
        for item in (r.json().get("results") or [])[:max_items]:
            t = item.get("title", "")
            desc = (item.get("description") or item.get("content", ""))[:500]
            result.append({
                "title": t,
                "title_ko": t,
                "description": desc,
                "summary_ko": desc,
                "summary_en": desc,
                "insight_ko": "", "insight_en": "",
                "action_ko": "", "action_en": "",
                "url": item.get("link", "#"),
                "source": item.get("source_id", "NewsData"),
                "published": (item.get("pubDate") or "")[:16],
                "region": "글로벌",
                "trust": get_trust("NewsData"),
                "tag": "",
            })
        return result
    except Exception:
        return []


@st.cache_data(ttl=1800, show_spinner=False)
def load_all_news(selected_cats: tuple, region_mode: str) -> pd.DataFrame:
    all_articles = []
    for cat_name in selected_cats:
        cfg = CATEGORY_CONFIG[cat_name]
        if region_mode in ["국내", "전체"]:
            for kw in cfg["naver_kw"]:
                arts = fetch_naver(kw, display=10)
                for a in arts:
                    a["category"] = cat_name
                all_articles.extend(arts)
        for src_name in cfg["rss_keys"]:
            if src_name not in RSS_SOURCES:
                continue
            rss_url, region = RSS_SOURCES[src_name]
            if region_mode == "국내" and "국내" not in region:
                continue
            if region_mode == "글로벌" and "국내" in region:
                continue
            items = fetch_rss(src_name, rss_url, region, max_items=10)
            for a in items:
                a["category"] = cat_name
            all_articles.extend(items)
        if region_mode in ["글로벌", "전체"]:
            items = fetch_newsdata(cfg["news_kw"])
            for a in items:
                a["category"] = cat_name
            all_articles.extend(items)
    for ins in CURATED_INSIGHTS:
        if ins["category"] in selected_cats and region_mode != "국내":
            all_articles.append({
                **ins,
                "description": ins.get("summary_ko", ""),
                "published": ins["published_str"],
                "trust": get_trust(ins["source"]),
            })
    df = pd.DataFrame(all_articles)
    if df.empty:
        return df
    df = df[df["title"].str.strip().str.len() > 5]
    df = df[~df["title"].str.contains("Removed|광고|\\[|undefined", na=False, regex=True)]
    # HR과 무관한 스포츠/정치 뉴스 등을 제외 (큐레이션 리포트는 항상 유지)
    keep_mask = df.apply(
        lambda r: bool(r.get("tag", "")) or is_hr_relevant(r.get("title", ""), r.get("description", "")),
        axis=1
    )
    df = df[keep_mask]
    df = df.drop_duplicates(subset=["title"])
    df["published_dt"] = pd.to_datetime(df["published"], errors="coerce")
    df["published_str"] = df["published_dt"].dt.strftime("%Y-%m-%d").fillna(
        df.get("published", "날짜 미상"))
    df = df.sort_values("published_dt", ascending=False, na_position="last")
    return df.reset_index(drop=True)

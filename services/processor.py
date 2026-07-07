import pandas as pd

POSITIVE_KW = [
    "채용확대","성장","혁신","상생","개선","우수","최고","증가","기록","돌파","신규",
    "활성화","강화","지원","협력","호황","도입","확대","인상","수상",
    "award","growth","record","hire","best","innovation","expansion",
    "success","increase","improve","launch","invest"
]
NEGATIVE_KW = [
    "파업","해고","분쟁","갈등","위반","과태료","소송","구조조정","감원","적자",
    "하락","감소","폐업","위기","처벌","논란","반발","거부","제재",
    "strike","layoff","lawsuit","penalty","conflict","decrease","cut","ban",
    "violation","dispute","crisis","protest","collapse","fine"
]
HOT_KW = [
    "최저임금","정년연장","근로기준법","육아휴직","주4일제","AI 채용","노란봉투법",
    "포괄임금","직장내괴롭힘","플랫폼노동","ESG","MZ노조","통상임금",
    "minimum wage","4-day work week","AI hiring","pay transparency",
    "labor reform","gig worker","DEI","quiet quitting"
]

def analyze(row):
    text = (str(row.get("title","")) + " " + str(row.get("description",""))).lower()
    pos  = sum(1 for k in POSITIVE_KW if k.lower() in text)
    neg  = sum(1 for k in NEGATIVE_KW if k.lower() in text)
    if neg > pos:
        sentiment = ("부정 / Negative", "#DC2626", "🔻")
    elif pos > neg:
        sentiment = ("긍정 / Positive", "#059669", "🔺")
    else:
        sentiment = ("중립 / Neutral",  "#D97706", "➖")
    is_hot = any(k.lower() in text for k in HOT_KW)
    return sentiment, is_hot

def enrich(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    results          = df.apply(analyze, axis=1)
    df["sentiment"]  = results.apply(lambda x: x[0][0])
    df["sent_color"] = results.apply(lambda x: x[0][1])
    df["sent_emoji"] = results.apply(lambda x: x[0][2])
    df["is_hot"]     = results.apply(lambda x: x[1])
    return df

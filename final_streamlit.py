import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import openai
import json

df = pd.read_csv("generated_diaries.csv")

df['date'] = pd.to_datetime(df['Diary Date'])
df['month'] = df['date'].dt.month
df['year'] = df['date'].dt.year

st.set_page_config(layout="wide")
st.title("월간 일기 통계")

st.sidebar.title("🗓️ 기간 선택")

selected_year = st.sidebar.selectbox("연도를 선택하세요", sorted(df['year'].unique()))
selected_month = st.sidebar.selectbox("월을 선택하세요", sorted(df[df['year'] == selected_year]['month'].unique()))


filtered_df = df[
    (df['year'] == selected_year) &
    (df['month'] == selected_month)
]

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    daily_count = filtered_df['date'].dt.day.value_counts().sort_index()
    fig = px.bar(x=daily_count.index, y=daily_count.values,
                 labels={'x': 'Day', 'y': 'Number of Diaries'},
                 title='일기 작성일')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    def parse_emotions(text):
        emotions = {'긍정': 0, '부정': 0, '중립': 0}
        if pd.notnull(text):
            for emo in emotions.keys():
                if emo in text:
                    emotions[emo] = 1
        return pd.Series(emotions)

    emotion_cols = filtered_df['grouped_emotion'].apply(parse_emotions)
    emotion_cols['date'] = filtered_df['date'].dt.date

    emotion_daily = emotion_cols.groupby('date').sum().reset_index()

    fig2 = px.line(
        emotion_daily,
        x='date',
        y=['긍정', '부정', '중립'],
        markers=True,
        labels={'value': 'Count', 'date': 'Date', 'variable': 'Emotion'},
        title='감정 흐름'
    )

    st.plotly_chart(fig2, use_container_width=True)

with col3:
    hourly_count = filtered_df['Hour'].value_counts().sort_index()
    fig3 = px.bar(x=hourly_count.index, y=hourly_count.values,
                  labels={'x': 'Hour', 'y': 'Number of Diaries'},
                  title='일기 작성 시간대')
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    text_data = " ".join(filtered_df['Diary Content'].dropna().values)
    wordcloud = WordCloud(width=800, height=400, background_color='white', font_path="./assets/NanumGothic-Regular.ttf").generate(text_data)

    fig4, ax = plt.subplots(figsize=(8, 4))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig4)

user_api_key = st.sidebar.text_input("🔑 OpenAI API 키 입력", type="password")
st.markdown(' ')

data = {
    'Year' : selected_year,
    'Month' : selected_month,
    'Emotions' : emotion_daily,
    'Diary Content' : filtered_df['Diary Content']
}

report_data_str = json.dumps(data, indent=2, default=str)

if st.sidebar.button("일기 요약 요청"):
    if not user_api_key:
        st.error("❗ OpenAI API 키를 입력해주세요.")
    else:
        try:
            prompt = f"""
한 달간의 일기를 요약해줘
추천할만한, 도움이 될만한 문구를 넣어줘
부정적인 감정이 많이 나타났다면 위로 문구를 넣어줘

---

# 일기 요약에 필요한 원본 데이터
{report_data_str}

---
아래와 같이 작성해줘 

{selected_month}월 한 달 간 일기 작성 수 : {len(filtered_df['date'].unique())}일
주 일기 작성 시간대 : {filtered_df['Hour'].mode().iloc[0]}시
추천할만한, 도움이 될만한 문구 또는 위로 문구
당신이 많이 쓰는 키워드 : 자주 나오는 키워드

---
자주 나오는 키워드는 {report_data_str}의 'Diary Content'에서 뽑아줘
추천할만한, 도움이 될만한 문구 또는 위로 문구는 소제목 없이 적어줘
{emotion_daily}에 나타나는 감정의 수에 따라 짧은 문장을 추가해줘 
예시) 이번달에는 부정적인 감정이 많이 보이네요.

다음은 사용자가 작성한 일기입니다.

---
[일기 내용]
{report_data_str}
---

당신은 심리학과 자기성찰을 전문으로 연구하는 고급 코치입니다.

이 일기의 내용을 바탕으로, 사용자의 **사고의 강점**과 **보완할 점**을 다음 기준에 맞춰 분석해 주세요.

- 감정 표현, 사고의 깊이, 사고의 유연성, 문제 해결 관점 등을 고려합니다.
- 강점은 명확하게 칭찬하며 구체적인 예시를 들어주세요.
- 보완할 점은 부드럽고 긍정적인 어조로 제안해 주세요 ("~하면 더 좋을 것 같아요"처럼).
- 절대 단정짓거나 부정적인 언어를 사용하지 않습니다.
- 전문적이면서도 친근한 톤을 유지합니다.
- 분석 결과는 "강점"과 "보완할 점"으로 각각 구분하여 제시합니다.

**[출력 예시]**
강점:
- 사용자가 감정을 솔직하게 표현하여 자기 인식을 잘하고 있습니다.
- 문제 상황을 논리적으로 정리하려는 사고 경향이 돋보입니다.

보완할 점:
- 때때로 부정적인 감정에 빠져 전반적인 맥락을 놓치는 경향이 있습니다.
- 감정의 원인을 다양한 관점에서 바라보는 연습을 하면 더 좋을 것 같습니다.


"""

            client = openai.OpenAI(api_key=user_api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            report = response.choices[0].message.content
            st.write(report)
        except Exception as e:
            st.error(f"📛 일기 요약 중 오류 발생: {e}")

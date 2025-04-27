# Streamlit 기반 대시보드: 사용자별 월간 감정 통계 및 리포트 자동화
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- API 키 입력 ---
st.sidebar.header("🔐 API Key 설정")
api_key = st.sidebar.text_input("OpenAI API Key 입력", type="password")

# --- 데이터 업로드 ---
st.title("📊 사용자별 월간 감정 분석 대시보드")
uploaded_file = st.file_uploader("CSV 형식의 정제된 감정 데이터 업로드", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['Diary Date'] = pd.to_datetime(df['Diary Date'], errors='coerce')
    df['Month'] = df['Diary Date'].dt.to_period('M').astype(str)

    # 사용자 선택
    user_ids = df['id'].dropna().unique()
    selected_id = st.selectbox("사용자를 선택하세요:", sorted(user_ids))

    # 필터링
    user_df = df[df['id'] == selected_id].copy()

    # 감정 카테고리 기준 집계
    monthly_stats = pd.crosstab(user_df['Month'], user_df['Emotion Category'])

    # 월간 변화선 그래프
    st.subheader(f"📈 사용자 {selected_id}의 월간 감정 변화")
    fig = px.line(monthly_stats, markers=True, title="월별 감정 빈도 추이")
    st.plotly_chart(fig)

    # 일기 형식별 감정 비율
    st.subheader("📘 일기 형식별 감정 분포")
    diary_type_dist = pd.crosstab(user_df['Diary Type'], user_df['Emotion Category'], normalize='index') * 100
    fig2 = go.Figure()
    for emotion in diary_type_dist.columns:
        fig2.add_trace(go.Bar(x=diary_type_dist.index, y=diary_type_dist[emotion], name=emotion))
    fig2.update_layout(barmode='stack', xaxis_title='일기 유형', yaxis_title='비율 (%)')
    st.plotly_chart(fig2)

    # 감정 총합 리포트
    st.subheader("📝 감정 리포트 요약")
    total_emotion = user_df['Emotion Category'].value_counts()
    st.write("#### 총 감정 분포:")
    st.dataframe(total_emotion.reset_index().rename(columns={'index': '감정 범주', 'Emotion Category': '빈도'}))

    # 리포트 다운로드 버튼
    report = total_emotion.reset_index().rename(columns={'index': '감정 범주', 'Emotion Category': '빈도'})
    report['사용자 ID'] = selected_id
    report['리포트 생성일'] = datetime.now().strftime('%Y-%m-%d')
    csv = report.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 리포트 다운로드 (CSV)", data=csv, file_name=f"{selected_id}_emotion_report.csv", mime='text/csv')

else:
    st.info("좌측 사이드바에서 API 키를 입력하고, 정제된 데이터를 업로드해주세요.")
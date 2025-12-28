import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Engagement Dashboard", layout="wide")

st.title("📊 Engagement Analytics Dashboard")

conn = sqlite3.connect("../server/engagement.db")

# =========================
# LOAD DATA
# =========================
df = pd.read_sql("""
SELECT s.responden, s.sesi, f.timestamp,
       f.engagement_level, f.fps, f.response_time
FROM frames f
JOIN sessions s ON f.session_id = s.id
""", conn)

if df.empty:
    st.warning("No data available")
    st.stop()

# =========================
# FILTER
# =========================
responden = st.selectbox("Select Responden", df["responden"].unique())
df = df[df["responden"] == responden]

# =========================
# METRICS
# =========================
col1, col2, col3 = st.columns(3)

col1.metric("Avg Engagement", round(df.engagement_level.mean(), 2))
col2.metric("High Engagement (%)", round((df.engagement_level >= 2).mean() * 100, 2))
col3.metric("Avg FPS", round(df.fps.mean(), 2))

# =========================
# CHARTS
# =========================
st.subheader("Engagement Over Time")
st.line_chart(df.set_index("timestamp")["engagement_level"])

st.subheader("Engagement Distribution")
st.bar_chart(df["engagement_level"].value_counts())

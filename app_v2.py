import os
os.environ["STREAMLIT_WATCH_FOR_CHANGES"] = "false"

import streamlit as st
import pandas as pd
import altair as alt

# 页面配置
st.set_page_config(
    page_title="Health Data Visualization System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 加载数据
@st.cache_data
def load_data():
    daily_df = pd.read_csv("data/merged_activity_sleep.csv")
    daily_df['ActivityDate'] = pd.to_datetime(daily_df['ActivityDate'])
    daily_df['Date'] = daily_df['ActivityDate'].dt.date

    hourly_steps = pd.read_csv("data/merged_hourly_steps.csv")
    hourly_steps['ActivityHour'] = pd.to_datetime(hourly_steps['ActivityHour'])
    hourly_steps['Date'] = hourly_steps['ActivityHour'].dt.date

    second_hr = pd.read_csv("data/merged_seconds_heartrate.csv")
    second_hr['Time'] = pd.to_datetime(second_hr['Time'])
    second_hr['Date'] = second_hr['Time'].dt.date

    minute_sleep = pd.read_csv("data/merged_minute_sleep.csv")
    minute_sleep['date'] = pd.to_datetime(minute_sleep['date'])
    minute_sleep['Date'] = minute_sleep['date'].dt.date

    return daily_df, hourly_steps, second_hr, minute_sleep

# 加载数据
daily_df, hourly_steps, second_hr, minute_sleep = load_data()

# 用户选择器
user_ids = sorted(daily_df['Id'].unique())
user_id = st.sidebar.selectbox("Select User", user_ids)

# 日期范围
min_date = daily_df['Date'].min()
max_date = daily_df['Date'].max()
start_date = st.sidebar.date_input("Start Date", min_value=min_date, max_value=max_date, value=min_date)
end_date = st.sidebar.date_input("End Date", min_value=min_date, max_value=max_date, value=max_date)

# 筛选数据
filtered_daily = daily_df[(daily_df['Id'] == user_id) &
                          (daily_df['Date'] >= start_date) &
                          (daily_df['Date'] <= end_date)]

# 页面选择
chart_type = st.sidebar.radio("Select View", ["Steps", "Sleep", "Heart Rate"])

# 图表渲染
if chart_type == "Steps":
    st.header("Steps")
    if filtered_daily.empty:
        st.warning("No step data found for selected user and date range.")
    else:
        date_select = alt.selection_point(fields=["Date"], on="click")
        daily_steps_chart = alt.Chart(filtered_daily).mark_bar().encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("TotalSteps:Q", title="Total Steps"),
            tooltip=["Date", "TotalSteps"],
            opacity=alt.condition(date_select, alt.value(1), alt.value(0.3))
        ).add_params(date_select).properties(height=300)

        hourly_user = hourly_steps[hourly_steps['Id'] == user_id]
        hourly_chart = alt.Chart(hourly_user).transform_filter(
            date_select
        ).mark_line().encode(
            x=alt.X("ActivityHour:T", title="Hour"),
            y=alt.Y("StepTotal:Q", title="Steps"),
            tooltip=["ActivityHour", "StepTotal"]
        ).properties(height=300)

        st.altair_chart(daily_steps_chart & hourly_chart, use_container_width=True)

elif chart_type == "Sleep":
    st.header("Sleep")
    if filtered_daily.empty:
        st.warning("No sleep data found for selected user and date range.")
    else:
        date_select = alt.selection_point(fields=["Date"], on="click")
        daily_sleep_chart = alt.Chart(filtered_daily).mark_bar().encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("TotalMinutesAsleep:Q", title="Minutes Asleep"),
            tooltip=["Date", "TotalMinutesAsleep"],
            opacity=alt.condition(date_select, alt.value(1), alt.value(0.3))
        ).add_params(date_select).properties(height=300)

        minute_user = minute_sleep[minute_sleep['Id'] == user_id]
        minute_chart = alt.Chart(minute_user).transform_filter(
            date_select
        ).mark_line().encode(
            x=alt.X("date:T", title="Time"),
            y=alt.Y("value:Q", title="Sleep Value"),
            tooltip=["date", "value"]
        ).properties(height=300)

        st.altair_chart(daily_sleep_chart & minute_chart, use_container_width=True)

elif chart_type == "Heart Rate":
    st.header("Heart Rate")
    available_dates = sorted(filtered_daily['Date'].unique())
    if not available_dates:
        st.warning("No data found for selected user and date range.")
    else:
        selected_day = st.selectbox("Select Day", options=available_dates)
        hr_user = second_hr[(second_hr['Id'] == user_id) & (second_hr['Date'] == selected_day)]

        if hr_user.empty:
            st.warning("No heart rate data available for this day.")
        else:
            chart = alt.Chart(hr_user).mark_line().encode(
                x=alt.X("Time:T", title="Time"),
                y=alt.Y("Value:Q", title="Heart Rate"),
                tooltip=["Time", "Value"]
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)

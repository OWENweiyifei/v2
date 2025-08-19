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

daily_df, hourly_steps, second_hr, minute_sleep = load_data()

# 提取选项
user_ids = sorted(daily_df['Id'].unique())
#date_options = sorted(daily_df['ActivityDate'].dt.strftime('%Y-%m-%d').unique())
date_options = sorted(daily_df['ActivityDate'].dt.date.unique())

# Sidebar 控件
st.sidebar.title("Control Panel")

# Select user
user_id = st.sidebar.selectbox("Select User：", user_ids, index=0)

# 选择起止日期
start_date = st.sidebar.date_input("Start Date:", value=min(date_options), min_value=min(date_options), max_value=max(date_options))
end_date = st.sidebar.date_input("End Date:", value=max(date_options), min_value=min(date_options), max_value=max(date_options))

chart_type = st.sidebar.selectbox("Select View:", [
    'Steps Overview',
    'Sleep Overview',
    'Heart Rate (Single Day)'
])

# 筛选数据
filtered_daily = daily_df[(daily_df['Id'] == user_id) & 
              (daily_df['ActivityDate'].dt.date >= start_date) & 
              (daily_df['ActivityDate'].dt.date <= end_date)]

# 页面标题
st.title("Health Data Visualization System")
st.markdown("Data Source: FitBit Fitness Tracker Data")


# 联动选择器（用于 Steps / Sleep 视图点击）
date_select = alt.selection_point(
    fields=['Date'], on='click', empty='none', clear='dblclick'
)

# 初始化 chart
chart = None

# === 视图类型 1：Steps Overview ===
if chart_type == 'Steps Overview':
    st.subheader("Daily Steps (Click to see hourly details)")

    # 主图：每日步数
    daily_steps_chart = alt.Chart(filtered_daily).mark_bar(
        color='#2196F3',size=13
    ).encode(
        x=alt.X('Date:T', title='Date',  axis = alt.Axis(format='%b %d')),
        y=alt.Y('TotalSteps:Q', title='Steps'),
        tooltip=['Date:T', 'TotalSteps']
    ).add_params(
        date_select
    ).properties(height=400)

    # 子图：所选日期的每小时步数
    hourly_chart = alt.Chart(hourly_steps).transform_filter(
        date_select
    ).transform_filter(
        alt.datum.Id == user_id
    ).mark_bar(color='#4FC3F7',size=13).encode(
        x=alt.X('ActivityHour:T', title='Hour',axis=alt.Axis(
    tickCount=24,
    labelAngle=0,
    labelOverlap=False,
    labelPadding=10,
    titlePadding=20
)),
        y=alt.Y('StepTotal:Q', title='Steps per Hour'),
        tooltip=['ActivityHour:T', 'StepTotal']
    ).properties(height=400)

    chart = daily_steps_chart & hourly_chart

# === 视图类型 2：Sleep Overview ===
elif chart_type == 'Sleep Overview':
    st.subheader("Daily Sleep Duration (Click to see minute-level details)")

    # 主图：每日睡眠
    daily_sleep_chart = alt.Chart(filtered_daily).mark_bar(
        color='#9C27B0', size=13
    ).encode(
        x=alt.X('Date:T', title='Date', axis = alt.Axis(format='%b %d')),
        y=alt.Y('TotalMinutesAsleep:Q', title='Minutes Asleep'),
        tooltip=['Date:T', 'TotalMinutesAsleep']
    ).add_params(
        date_select
    ).properties(height=400)

    # 子图：所选日期的分钟级睡眠
    minute_chart = alt.Chart(minute_sleep).transform_filter(
        date_select
    ).transform_filter(
        alt.datum.Id == user_id
    ).mark_area(
        color='#CE93D8', opacity=0.5
    ).encode(
        x=alt.X('date:T', title='Time', axis=alt.Axis(
    tickCount=24,
    labelAngle=0,
    labelOverlap=False,
    labelPadding=10,
    titlePadding=20
)),
        y=alt.Y('value:Q', title='Sleep Level (Encoded)'),
        tooltip=['date:T', 'value']
    ).properties(height=400)

    chart = daily_sleep_chart & minute_chart

# === 视图类型 3：Heart Rate (Single Day) ===
elif chart_type == 'Heart Rate (Single Day)':
    st.subheader("Heart Rate View (Select a day)")

    # 限定选择范围内可选日期
    hr_dates = sorted([d for d in date_options if start_date <= d <= end_date])
    selected_day = st.sidebar.selectbox("Select Day for Heart Rate View:", options=hr_dates)

    hr_filtered = second_hr[
        (second_hr['Id'] == user_id) &
        (second_hr['Date'] == selected_day)
    ]

    if hr_filtered.empty:
        st.warning(f"No heart rate data available for {selected_day}.")
    else:
        chart = alt.Chart(hr_filtered).mark_line(color='#F44336').encode(
            x=alt.X('Time:T', title='Time', axis=alt.Axis(format='%H:%M')),
            y=alt.Y('Value:Q', title='Heart Rate (bpm)'),
            tooltip=['Time:T', 'Value']
        ).properties(height=400, title=f'Heart Rate on {selected_day}')

# 展示图表
if chart is not None:
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("Please select a view type to begin visualization.")


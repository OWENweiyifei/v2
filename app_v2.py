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

# 用户选择器
user_ids = sorted(daily_df['Id'].unique())
user_id = st.sidebar.selectbox("Select User：", user_ids, index=0)

# 日期选择
min_date = daily_df['Date'].min()
max_date = daily_df['Date'].max()
start_date = st.sidebar.date_input("Start Date", min_value=min_date, max_value=max_date, value=min_date)
end_date = st.sidebar.date_input("End Date", min_value=min_date, max_value=max_date, value=max_date)


# 筛选数据
filtered_daily = daily_df[(daily_df['Id'] == user_id) & 
              (daily_df['Date'] >= start_date) & 
              (daily_df['Date'] <= end_date)]

#视图选择
chart_type = st.sidebar.radio("Select View:", ['Steps','Sleep','Heart Rate'])

# 页面标题
st.title("Health Data Visualization System")
st.markdown("Data Source: FitBit Fitness Tracker Data")

# 初始化 chart
chart = None

# === 视图类型 1：Steps ===
if chart_type == 'Steps':
    st.subheader("Steps (Click to see details)")
    if filtered_daily.empty:
        st.warning("No step data found for selected user and date range.")
    else:
    # 主图：每日步数
        date_select = alt.selection_point(fields=["Date"], on="click",clear='dblclick')
        daily_steps_chart = alt.Chart(filtered_daily).mark_bar(color='#2196F3',size=13).encode(
            x=alt.X('Date:T', title='Date',  axis = alt.Axis(format='%b %d')),
            y=alt.Y('TotalSteps:Q', title='Steps'),
            tooltip=['Date', 'TotalSteps'],
            opacity=alt.condition(date_select, alt.value(1), alt.value(0.3))
    ).add_params(date_select).properties(height=400)

    # 子图：所选日期的每小时步数
        hourly_user = hourly_steps[hourly_steps['Id'] == user_id]
        hourly_chart = alt.Chart(hourly_user).transform_filter(
        date_select
        ).mark_line(color='#4FC3F7').encode(
            x=alt.X('ActivityHour:T', title='Hour'),
            y=alt.Y('StepTotal:Q', title='Steps'),
            tooltip=['ActivityHour:T', 'StepTotal']
        ).properties(height=400)

        st.altair_chart(daily_steps_chart & hourly_chart, use_container_width=True)

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


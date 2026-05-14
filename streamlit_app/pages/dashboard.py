"""
Room Booking Analytics Dashboard
Management-level decision support dashboard built with Streamlit + Plotly.
"""

import os
from datetime import datetime, timedelta, date

import pandas as pd
import plotly.express as px
import streamlit as st
from django.utils import timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import fetch_all_bookings, fetch_all_rooms

BUSINESS_HOURS_PER_DAY = 10  # 08:00 - 18:00
COLOR_SEQUENCE = ["#4C78A8", "#72B7B2", "#54A24B", "#E45756", "#F58518", "#B279A2"]


st.set_page_config(
    page_title="Room Booking Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main {padding: 0.5rem 1rem;}
    .stMetric {
        background-color: #f8fafc;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
    }
    .block-container {padding-top: 1rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def _normalize_datetime_column(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series([], dtype="datetime64[ns]")
    values = pd.to_datetime(df[col], errors="coerce")
    if getattr(values.dt, "tz", None) is not None:
        return values.dt.tz_localize(None)
    return values


@st.cache_data(ttl=300)
def load_dataframes() -> tuple[pd.DataFrame, pd.DataFrame]:
    # Use booking data retrieved from the database module
    from database import fetch_all_bookings, fetch_all_rooms

    booking_rows = fetch_all_bookings()
    room_rows = fetch_all_rooms()

    df_bookings = pd.DataFrame(booking_rows)
    df_rooms = pd.DataFrame(room_rows)

    if not df_bookings.empty:
        # Re-map columns from fetch_all_bookings to what the dashboard expects
        if "user_name" in df_bookings.columns:
            df_bookings["user__first_name"] = df_bookings["user_name"]
            df_bookings["user__last_name"] = ""
        if "user_email" in df_bookings.columns:
            df_bookings["user__email"] = df_bookings["user_email"]
        if "room_name" in df_bookings.columns:
            df_bookings["room__name"] = df_bookings["room_name"]
        if "room_number" in df_bookings.columns:
            df_bookings["room__room_number"] = df_bookings["room_number"]
            
        # Extract fake IDs if not provided
        df_bookings["user_id"] = df_bookings["user_email"]
        # Try to map room_id from df_rooms
        if not df_rooms.empty and "room_number" in df_rooms.columns and "room_number" in df_bookings.columns:
            room_map = dict(zip(df_rooms["room_number"], df_rooms["id"]))
            df_bookings["room_id"] = df_bookings["room_number"].map(room_map)
        else:
            df_bookings["room_id"] = 1

        df_bookings["start_time"] = _normalize_datetime_column(df_bookings, "start_time")
        df_bookings["end_time"] = _normalize_datetime_column(df_bookings, "end_time")
        df_bookings["created_at"] = _normalize_datetime_column(df_bookings, "created_at")
        df_bookings["duration_hours"] = (
            (df_bookings["end_time"] - df_bookings["start_time"]).dt.total_seconds() / 3600
        ).clip(lower=0)
        df_bookings["date"] = df_bookings["start_time"].dt.date
        df_bookings["hour"] = df_bookings["start_time"].dt.hour
        df_bookings["day_of_week"] = df_bookings["start_time"].dt.day_name()
        df_bookings["month"] = df_bookings["start_time"].dt.to_period("M").astype(str)
        df_bookings["week_period"] = df_bookings["start_time"].dt.to_period("W").astype(str)
        df_bookings["user_name"] = (
            (df_bookings["user__first_name"].fillna("") + " " + df_bookings["user__last_name"].fillna(""))
            .str.strip()
            .replace("", pd.NA)
            .fillna(df_bookings["user__email"])
        )
        df_bookings["room_label"] = (
            df_bookings["room__name"].fillna("Unknown Room")
            + " ("
            + df_bookings["room__room_number"].fillna("N/A")
            + ")"
        )

    return df_bookings, df_rooms


def build_filters(df_bookings: pd.DataFrame, df_rooms: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    st.sidebar.header("🔍 Filters")

    today = timezone.now().date()

    data_min_date = None
    data_max_date = None
    if not df_bookings.empty:
        data_min_date = df_bookings["start_time"].dt.date.min()
        data_max_date = df_bookings["start_time"].dt.date.max()

    time_option = st.sidebar.selectbox(
        "Time Range",
        ["Today", "Last 7 days", "Last 30 days", "Custom Range"],
        index=2,
    )

    if time_option == "Today":
        start_date = today
        end_date = today
    elif time_option == "Last 7 days":
        start_date = today - timedelta(days=6)
        end_date = today
    elif time_option == "Last 30 days":
        start_date = today - timedelta(days=29)
        end_date = today
    else:
        if data_min_date and data_max_date:
            default_start = min(data_min_date, today)
            default_end = max(data_max_date, today)
        else:
            default_start = today - timedelta(days=29)
            default_end = today

        max_picker_date = max(default_end, today)
        picked = st.sidebar.date_input(
            "Custom Date Range",
            value=(default_start, default_end),
            min_value=date(2020, 1, 1),
            max_value=max_picker_date,
        )
        if isinstance(picked, tuple) and len(picked) == 2:
            start_date, end_date = picked
        else:
            start_date = picked
            end_date = picked

    if data_min_date and data_max_date:
        st.sidebar.caption(f"Data available from {data_min_date} to {data_max_date}")

    room_options = []
    if not df_rooms.empty:
        room_options = sorted(
            (df_rooms["name"].fillna("Unknown") + " (" + df_rooms["room_number"].fillna("N/A") + ")").unique()
        )

    selected_rooms = st.sidebar.multiselect("Room Filter", options=room_options, default=[])

    user_options = []
    if not df_bookings.empty and "user_name" in df_bookings.columns:
        user_options = sorted(df_bookings["user_name"].dropna().astype(str).unique().tolist())
    selected_users = st.sidebar.multiselect("User Filter", options=user_options, default=[])

    status_options = []
    if not df_bookings.empty:
        status_options = sorted(df_bookings["status"].dropna().astype(str).unique().tolist())
    selected_statuses = st.sidebar.multiselect("Booking Status", options=status_options, default=status_options)

    filtered_df = df_bookings.copy()
    if not filtered_df.empty:
        filtered_df = filtered_df[
            (filtered_df["start_time"].dt.date >= start_date)
            & (filtered_df["start_time"].dt.date <= end_date)
        ]
        if selected_rooms:
            filtered_df = filtered_df[filtered_df["room_label"].isin(selected_rooms)]
        if selected_users:
            filtered_df = filtered_df[filtered_df["user_name"].isin(selected_users)]
        if selected_statuses:
            filtered_df = filtered_df[filtered_df["status"].isin(selected_statuses)]
        else:
            filtered_df = filtered_df.iloc[0:0]

    context = {
        "time_option": time_option,
        "start_date": start_date,
        "end_date": end_date,
        "data_min_date": data_min_date,
        "data_max_date": data_max_date,
    }
    return filtered_df, context


def available_hours_total(total_rooms: int, start_date: date, end_date: date) -> float:
    days = max((end_date - start_date).days + 1, 1)
    return float(total_rooms * days * BUSINESS_HOURS_PER_DAY)


def section_overview(df: pd.DataFrame, df_rooms: pd.DataFrame, context: dict) -> dict:
    st.header("Overview (KPIs)")
    with st.container():
        total_bookings = int(len(df))
        confirmed_count = int((df["status"] == "confirmed").sum()) if not df.empty else 0
        cancelled_count = int((df["status"] == "cancelled").sum()) if not df.empty else 0
        cancellation_rate = _safe_divide(cancelled_count * 100, total_bookings)

        total_rooms = int(len(df_rooms)) if not df_rooms.empty else 0
        total_booked_hours = float(df["duration_hours"].sum()) if not df.empty else 0.0
        total_available_hours = available_hours_total(total_rooms, context["start_date"], context["end_date"])
        room_utilization_rate = _safe_divide(total_booked_hours * 100, total_available_hours)

        active_users = int(df["user_id"].nunique()) if not df.empty else 0
        avg_duration = float(df["duration_hours"].mean()) if not df.empty else 0.0

        kpi_cols_1 = st.columns(4)
        kpi_cols_2 = st.columns(4)

        with kpi_cols_1[0]:
            st.metric("Total Bookings", f"{total_bookings:,}")
        with kpi_cols_1[1]:
            st.metric("Total Confirmed Bookings", f"{confirmed_count:,}")
        with kpi_cols_1[2]:
            st.metric("Total Cancelled Bookings", f"{cancelled_count:,}")
        with kpi_cols_1[3]:
            st.metric("Cancellation Rate (%)", f"{cancellation_rate:.1f}%")

        with kpi_cols_2[0]:
            st.metric("Total Rooms", f"{total_rooms:,}")
        with kpi_cols_2[1]:
            st.metric("Room Utilization Rate (%)", f"{room_utilization_rate:.1f}%")
        with kpi_cols_2[2]:
            st.metric("Active Users", f"{active_users:,}")
        with kpi_cols_2[3]:
            st.metric("Average Booking Duration (hours)", f"{avg_duration:.2f}")

    return {
        "total_bookings": total_bookings,
        "confirmed_count": confirmed_count,
        "cancelled_count": cancelled_count,
        "cancellation_rate": cancellation_rate,
        "total_rooms": total_rooms,
        "total_booked_hours": total_booked_hours,
        "total_available_hours": total_available_hours,
        "room_utilization_rate": room_utilization_rate,
    }


def section_booking_trends(df: pd.DataFrame):
    st.header("Booking Trends")
    if df.empty:
        st.info("No booking data available for the selected filters.")
        return

    with st.container():
        trend_cols = st.columns(2)

        with trend_cols[0]:
            last_30_start = (df["start_time"].max() - pd.Timedelta(days=29)).date()
            daily_30 = (
                df[df["start_time"].dt.date >= last_30_start]
                .groupby("date")
                .size()
                .reset_index(name="bookings")
            )
            daily_30["date"] = pd.to_datetime(daily_30["date"])
            fig_daily = px.line(
                daily_30,
                x="date",
                y="bookings",
                title="Bookings per Day (Last 30 Days)",
                markers=True,
                color_discrete_sequence=[COLOR_SEQUENCE[0]],
            )
            fig_daily.update_layout(xaxis_title="Date", yaxis_title="Bookings")
            st.plotly_chart(fig_daily, use_container_width=True)

        with trend_cols[1]:
            start_ts = df["start_time"]
            if start_ts.empty:
                this_week_count = 0
                last_week_count = 0
            else:
                latest = start_ts.max().date()
                this_monday = latest - timedelta(days=latest.weekday())
                last_monday = this_monday - timedelta(days=7)
                this_week_count = int(((start_ts.dt.date >= this_monday) & (start_ts.dt.date <= latest)).sum())
                last_week_count = int(
                    ((start_ts.dt.date >= last_monday) & (start_ts.dt.date < this_monday)).sum()
                )

            weekly_compare = pd.DataFrame(
                {"period": ["Last Week", "This Week"], "bookings": [last_week_count, this_week_count]}
            )
            fig_week = px.bar(
                weekly_compare,
                x="period",
                y="bookings",
                title="Weekly Comparison: This Week vs Last Week",
                color="period",
                color_discrete_sequence=[COLOR_SEQUENCE[2], COLOR_SEQUENCE[1]],
            )
            fig_week.update_layout(showlegend=False, xaxis_title="", yaxis_title="Bookings")
            st.plotly_chart(fig_week, use_container_width=True)

        trend_cols_2 = st.columns(2)

        with trend_cols_2[0]:
            monthly = df.groupby("month").size().reset_index(name="bookings").sort_values("month")
            fig_monthly = px.line(
                monthly,
                x="month",
                y="bookings",
                title="Monthly Booking Trend",
                markers=True,
                color_discrete_sequence=[COLOR_SEQUENCE[3]],
            )
            fig_monthly.update_layout(xaxis_title="Month", yaxis_title="Bookings")
            st.plotly_chart(fig_monthly, use_container_width=True)

        with trend_cols_2[1]:
            cancel_trend = (
                df.assign(is_cancelled=df["status"].eq("cancelled").astype(int))
                .groupby("date", as_index=False)["is_cancelled"]
                .sum()
            )
            cancel_trend["date"] = pd.to_datetime(cancel_trend["date"])
            fig_cancel = px.line(
                cancel_trend,
                x="date",
                y="is_cancelled",
                title="Cancellation Trend Over Time",
                markers=True,
                color_discrete_sequence=[COLOR_SEQUENCE[4]],
            )
            fig_cancel.update_layout(xaxis_title="Date", yaxis_title="Cancelled Bookings")
            st.plotly_chart(fig_cancel, use_container_width=True)


def section_room_intelligence(df: pd.DataFrame, df_rooms: pd.DataFrame, context: dict):
    st.header("Room Intelligence")
    if df_rooms.empty:
        st.info("No rooms available.")
        return

    with st.container():
        room_usage = (
            df.groupby(["room_id", "room_label"], as_index=False)
            .agg(booking_count=("id", "count"), booked_hours=("duration_hours", "sum"))
            if not df.empty
            else pd.DataFrame(columns=["room_id", "room_label", "booking_count", "booked_hours"])
        )

        base_rooms = df_rooms.copy()
        base_rooms["room_label"] = (
            base_rooms["name"].fillna("Unknown Room") + " (" + base_rooms["room_number"].fillna("N/A") + ")"
        )
        merged = base_rooms[["id", "room_label"]].merge(
            room_usage[["room_id", "booking_count", "booked_hours"]],
            left_on="id",
            right_on="room_id",
            how="left",
        )
        merged["booking_count"] = pd.to_numeric(merged["booking_count"], errors="coerce").fillna(0).astype(int)
        merged["booked_hours"] = pd.to_numeric(merged["booked_hours"], errors="coerce").fillna(0.0)

        days = max((context["end_date"] - context["start_date"]).days + 1, 1)
        available_per_room = float(days * BUSINESS_HOURS_PER_DAY)
        merged["utilization_pct"] = merged["booked_hours"].apply(
            lambda hrs: min(_safe_divide(hrs * 100, available_per_room), 100.0)
        )
        merged["idle_time_pct"] = 100 - merged["utilization_pct"]

        top_bottom_cols = st.columns(2)

        with top_bottom_cols[0]:
            top_5 = merged.sort_values(["booking_count", "utilization_pct"], ascending=False).head(5)
            fig_top = px.bar(
                top_5,
                x="booking_count",
                y="room_label",
                orientation="h",
                title="Top 5 Most Booked Rooms",
                color="booking_count",
                color_continuous_scale="Blues",
            )
            fig_top.update_layout(xaxis_title="Bookings", yaxis_title="Room")
            st.plotly_chart(fig_top, use_container_width=True)

        with top_bottom_cols[1]:
            bottom_5 = merged.sort_values(["booking_count", "utilization_pct"], ascending=True).head(5)
            fig_bottom = px.bar(
                bottom_5,
                x="booking_count",
                y="room_label",
                orientation="h",
                title="Bottom 5 Least Used Rooms",
                color="booking_count",
                color_continuous_scale="Oranges",
            )
            fig_bottom.update_layout(xaxis_title="Bookings", yaxis_title="Room")
            st.plotly_chart(fig_bottom, use_container_width=True)

        util_cols = st.columns(2)

        with util_cols[0]:
            util_room = merged.sort_values("utilization_pct", ascending=False)
            fig_room_util = px.bar(
                util_room,
                x="room_label",
                y="utilization_pct",
                title="Room Utilization Rate per Room",
                color="utilization_pct",
                color_continuous_scale="Viridis",
            )
            fig_room_util.update_layout(xaxis_title="Room", yaxis_title="Utilization (%)")
            fig_room_util.update_xaxes(tickangle=35)
            st.plotly_chart(fig_room_util, use_container_width=True)

        with util_cols[1]:
            idle_room = merged.sort_values("idle_time_pct", ascending=False)
            fig_idle = px.bar(
                idle_room,
                x="room_label",
                y="idle_time_pct",
                title="Idle Time Percentage per Room",
                color="idle_time_pct",
                color_continuous_scale="Reds",
            )
            fig_idle.update_layout(xaxis_title="Room", yaxis_title="Idle Time (%)")
            fig_idle.update_xaxes(tickangle=35)
            st.plotly_chart(fig_idle, use_container_width=True)

        st.subheader("Heatmap: Day of Week vs Hour of Day Usage")
        usage_source = df[df["status"].eq("confirmed")] if not df.empty else df
        if usage_source.empty:
            st.info("No confirmed bookings to generate usage heatmap.")
        else:
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            heat = usage_source.groupby(["day_of_week", "hour"]).size().reset_index(name="bookings")
            heat["day_of_week"] = pd.Categorical(heat["day_of_week"], categories=day_order, ordered=True)
            pivot = heat.pivot(index="day_of_week", columns="hour", values="bookings").fillna(0).reindex(day_order)
            fig_heat = px.imshow(
                pivot,
                labels={"x": "Hour of Day", "y": "Day of Week", "color": "Bookings"},
                title="Day vs Hour Room Usage Heatmap",
                aspect="auto",
                color_continuous_scale="YlGnBu",
            )
            st.plotly_chart(fig_heat, use_container_width=True)


def section_user_intelligence(df: pd.DataFrame):
    st.header("User Intelligence")
    if df.empty:
        st.info("No booking data available for user analysis.")
        return

    with st.container():
        user_stats = (
            df.groupby(["user_id", "user_name"], as_index=False)
            .agg(booking_count=("id", "count"), avg_duration_hours=("duration_hours", "mean"))
            .sort_values("booking_count", ascending=False)
        )

        repeat_users = int((user_stats["booking_count"] > 1).sum())
        repeat_rate = _safe_divide(repeat_users * 100, len(user_stats))

        metric_cols = st.columns(3)
        with metric_cols[0]:
            st.metric("Users with Repeat Bookings", f"{repeat_users:,}")
        with metric_cols[1]:
            st.metric("Repeat Booking Rate", f"{repeat_rate:.1f}%")
        with metric_cols[2]:
            st.metric("Average Bookings per User", f"{user_stats['booking_count'].mean():.2f}")

        chart_cols = st.columns(2)

        with chart_cols[0]:
            top_users = user_stats.head(5)
            fig_top_users = px.bar(
                top_users.sort_values("booking_count", ascending=True),
                x="booking_count",
                y="user_name",
                orientation="h",
                title="Top 5 Users by Booking Count",
                color="booking_count",
                color_continuous_scale="Teal",
            )
            fig_top_users.update_layout(xaxis_title="Bookings", yaxis_title="User")
            st.plotly_chart(fig_top_users, use_container_width=True)

        with chart_cols[1]:
            avg_user_duration = user_stats.sort_values("avg_duration_hours", ascending=False).head(10)
            fig_user_duration = px.bar(
                avg_user_duration.sort_values("avg_duration_hours", ascending=True),
                x="avg_duration_hours",
                y="user_name",
                orientation="h",
                title="Average Booking Duration per User",
                color="avg_duration_hours",
                color_continuous_scale="Purples",
            )
            fig_user_duration.update_layout(xaxis_title="Avg Duration (hours)", yaxis_title="User")
            st.plotly_chart(fig_user_duration, use_container_width=True)

        if "user__department" in df.columns and df["user__department"].notna().any():
            dept_dist = (
                df.assign(department=df["user__department"].fillna("Unspecified").replace("", "Unspecified"))
                .groupby("department")
                .size()
                .reset_index(name="bookings")
                .sort_values("bookings", ascending=False)
            )
            fig_dept = px.bar(
                dept_dist,
                x="department",
                y="bookings",
                title="Booking Distribution by Department",
                color="bookings",
                color_continuous_scale="Cividis",
            )
            fig_dept.update_layout(xaxis_title="Department", yaxis_title="Bookings")
            fig_dept.update_xaxes(tickangle=35)
            st.plotly_chart(fig_dept, use_container_width=True)
        else:
            st.info("Department data is not available for current filtered bookings.")


def section_booking_duration_analysis(df: pd.DataFrame):
    st.header("Booking Duration Analysis")
    if df.empty:
        st.info("No booking data available for duration analysis.")
        return

    with st.container():
        duration_cols = st.columns(3)
        with duration_cols[0]:
            st.metric("Longest Booking", f"{df['duration_hours'].max():.2f} h")
        with duration_cols[1]:
            st.metric("Shortest Booking", f"{df['duration_hours'].min():.2f} h")
        with duration_cols[2]:
            st.metric("Average Booking Duration", f"{df['duration_hours'].mean():.2f} h")

        fig_hist = px.histogram(
            df,
            x="duration_hours",
            nbins=20,
            title="Histogram of Booking Duration (Hours)",
            color_discrete_sequence=[COLOR_SEQUENCE[0]],
        )
        fig_hist.update_layout(xaxis_title="Duration (hours)", yaxis_title="Number of Bookings")
        st.plotly_chart(fig_hist, use_container_width=True)


def section_operational_insights(df: pd.DataFrame, kpis: dict):
    st.header("Operational Insights")
    if df.empty:
        st.info("No booking data available for operational insights.")
        return

    with st.container():
        confirmed_df = df[df["status"].eq("confirmed")]
        source = confirmed_df if not confirmed_df.empty else df

        hour_count = source.groupby("hour").size().reset_index(name="bookings")
        day_count = source.groupby("day_of_week").size().reset_index(name="bookings")

        peak_hour = int(hour_count.sort_values("bookings", ascending=False).iloc[0]["hour"])
        peak_hour_bookings = int(hour_count.sort_values("bookings", ascending=False).iloc[0]["bookings"])

        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_count["day_of_week"] = pd.Categorical(day_count["day_of_week"], categories=day_order, ordered=True)
        day_count = day_count.sort_values("bookings", ascending=False)
        peak_day = str(day_count.iloc[0]["day_of_week"])

        efficiency = _safe_divide(kpis["total_booked_hours"] * 100, kpis["total_available_hours"])

        ops_cols = st.columns(3)
        with ops_cols[0]:
            st.metric("Peak Usage Hour", f"{peak_hour:02d}:00")
        with ops_cols[1]:
            st.metric("Peak Day of Week", peak_day)
        with ops_cols[2]:
            st.metric("Efficiency Score", f"{efficiency:.1f}%")

        recommendations = []
        if kpis["room_utilization_rate"] < 40:
            recommendations.append(
                "Utilization is below 40%; improve room awareness through internal communication and booking campaigns."
            )
        if kpis["cancellation_rate"] > 30:
            recommendations.append(
                "Cancellation rate is above 30%; review booking policy, confirmation reminders, and cancellation windows."
            )

        if len(hour_count) > 0:
            top_two_share = _safe_divide(
                hour_count.sort_values("bookings", ascending=False).head(2)["bookings"].sum() * 100,
                hour_count["bookings"].sum(),
            )
            if top_two_share >= 60:
                recommendations.append(
                    "Peak demand is concentrated in 2 hours; consider load-balancing via staggered scheduling incentives."
                )

        if recommendations:
            for item in recommendations:
                st.warning(item)
        else:
            st.info("Operational indicators are balanced for the selected filters.")

        st.caption(f"Peak hour currently has {peak_hour_bookings} bookings in the selected range.")


def main():
    if not st.session_state.get("authenticated", False):
        st.warning("⚠️ Access Denied. Please log in first.")
        st.stop()

    st.title("📊 Room Booking Analytics Dashboard")

    try:
        with st.spinner("Loading analytics data..."):
            df_bookings, df_rooms = load_dataframes()
    except Exception as exc:
        st.error(f"Failed to load data from database: {exc}")
        return

    if df_bookings.empty:
        st.info("No booking records found yet. KPIs and charts will appear when bookings are created.")

    filtered_df, context = build_filters(df_bookings, df_rooms)

    if not df_bookings.empty and filtered_df.empty:
        data_min = context.get("data_min_date")
        data_max = context.get("data_max_date")
        st.warning(
            "No data matched the selected filters. "
            f"Try Custom Range. Available booking dates: {data_min} to {data_max}."
        )

    st.markdown("---")
    kpis = section_overview(filtered_df, df_rooms, context)
    st.markdown("---")
    section_booking_trends(filtered_df)
    st.markdown("---")
    section_room_intelligence(filtered_df, df_rooms, context)
    st.markdown("---")
    section_user_intelligence(filtered_df)
    st.markdown("---")
    section_booking_duration_analysis(filtered_df)
    st.markdown("---")
    section_operational_insights(filtered_df, kpis)

    st.markdown("---")
    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


if __name__ == "__main__":
    main()

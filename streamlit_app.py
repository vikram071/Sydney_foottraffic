import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as gg
from plotly.subplots import make_subplots
import pydeck as pdk
import time
from datetime import datetime

from db import init_db, seed_baseline_history_if_empty, DB_FILE
from analytics import (
    get_latest_metrics,
    get_vehicle_occupancy_df,
    get_station_foot_traffic_df,
    get_hourly_commute_trends_df,
    get_animated_timeline_df,
    get_mode_breakdown_df,
    get_station_congestion_heatmap_df,
    get_service_alerts_df
)
from ml_models import train_time_series_forecaster, get_route_commute_benchmark_df

# Page Configuration
st.set_page_config(
    page_title="Sydney Transport Intelligence | Live Foot Traffic & ML Platform",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize and seed database if necessary
init_db(DB_FILE)
seed_baseline_history_if_empty(DB_FILE)

# Custom Styling (Dark Obsidian Glassmorphism)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Background & Cards */
    .stApp {
        background-color: #0B0F19;
        color: #F8FAFC;
    }
    
    .kpi-card {
        background: rgba(17, 24, 39, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .kpi-card:hover {
        border-color: rgba(6, 182, 212, 0.4);
        transform: translateY(-2px);
    }
    .kpi-label {
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94A3B8;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 800;
        color: #06B6D4;
        line-height: 1.2;
    }
    .kpi-sub {
        font-size: 12px;
        color: #64748B;
        margin-top: 4px;
    }
    
    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
    }
    .badge-heavy { background: rgba(244, 63, 94, 0.2); color: #F43F5E; border: 1px solid #F43F5E; }
    .badge-busy { background: rgba(249, 115, 22, 0.2); color: #F97316; border: 1px solid #F97316; }
    .badge-mod { background: rgba(245, 158, 11, 0.2); color: #F59E0B; border: 1px solid #F59E0B; }
    .badge-low { background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid #10B981; }

    /* Section Containers */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Colors
MODE_COLORS = {
    "Sydney Trains": [6, 182, 212],    # Electric Cyan
    "Sydney Metro": [139, 92, 246],    # Deep Violet
    "Sydney Buses": [59, 130, 246],    # Cobalt Blue
    "Sydney Ferries": [16, 185, 129],  # Neon Emerald
    "Light Rail": [245, 158, 11]       # Amber
}

MODE_HEX = {
    "Sydney Trains": "#06B6D4",
    "Sydney Metro": "#8B5CF6",
    "Sydney Buses": "#3B82F6",
    "Sydney Ferries": "#10B981",
    "Light Rail": "#F59E0B"
}

# Sidebar Navigation & Filters
st.sidebar.image("https://img.icons8.com/isometric/96/subway.png", width=64)
st.sidebar.title("Sydney Transport AI")
st.sidebar.caption("Real-Time Foot Traffic & ML Analytics Platform")

metrics = get_latest_metrics(DB_FILE)

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Data Filters")
selected_mode = st.sidebar.selectbox("Transport Mode", ["ALL", "Sydney Trains", "Sydney Metro", "Sydney Buses", "Sydney Ferries", "Light Rail"])
selected_region = st.sidebar.selectbox("Geographic Region", ["ALL", "CBD", "Western Sydney", "North Shore", "South/East", "Inner West", "Airport Corridor"])

st.sidebar.markdown("---")
st.sidebar.subheader("📡 Ingestion Status")
st.sidebar.markdown(f"**Status:** <span class='badge badge-low'>ACTIVE (30-MIN POLL)</span>", unsafe_allow_html=True)
st.sidebar.markdown(f"**Database:** `{DB_FILE}`")
st.sidebar.markdown(f"**Last Sync:** `{metrics.get('timestamp', 'N/A')}`")

if st.sidebar.button("🔄 Trigger Live Polling Job"):
    from collector import run_polling_job
    with st.spinner("Polling TfNSW endpoints..."):
        run_polling_job(DB_FILE)
    st.sidebar.success("Polling complete!")
    st.rerun()

# Title Header
st.title("🚆 Sydney Transport Intelligence Platform")
st.markdown("Real-time TfNSW GTFS-R fleet tracking, station foot traffic density, and Ridge ML time-series forecasting.")

# Executive KPI Cards
st.markdown("### 📊 Executive Overview")
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Active Fleet</div>
        <div class="kpi-value">{metrics.get('active_vehicles', 0):,}</div>
        <div class="kpi-sub">Vehicles tracked across Sydney</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Fleet Occupancy</div>
        <div class="kpi-value">{metrics.get('avg_occupancy_pct', 0)}%</div>
        <div class="kpi-sub">{metrics.get('congested_vehicles', 0)} vehicles at high capacity</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Busiest Interchange</div>
        <div class="kpi-value" style="font-size: 20px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">{metrics.get('busiest_station', 'Central')}</div>
        <div class="kpi-sub">Traffic Index: <b style="color:#F59E0B;">{metrics.get('busiest_station_index', 0)} / 100</b></div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">On-Time Performance</div>
        <div class="kpi-value">{metrics.get('on_time_pct', 94.2)}%</div>
        <div class="kpi-sub">Network avg delay: {metrics.get('network_avg_delay_sec', 0)}s</div>
    </div>
    """, unsafe_allow_html=True)

with kpi5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Parramatta Corridor</div>
        <div class="kpi-value">{metrics.get('parramatta_commute_min', 28.5)}m</div>
        <div class="kpi-sub">Delay: +{metrics.get('parramatta_delay_min', 2.5)}m (Base: 26m)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# FEATURE: Animated 24-Hour Traffic Flow Player
st.markdown("### 🎬 Animated 24-Hour Sydney Traffic Flow Movement")
st.caption("Play or drag the 24-hour timeline slider to visualize how foot traffic density shifts across Sydney interchanges throughout the day.")

anim_df = get_animated_timeline_df(DB_FILE)

if not anim_df.empty:
    anim_col1, anim_col2 = st.columns([1, 4])
    
    with anim_col1:
        play_speed = st.slider("Animation Speed (sec/frame)", 0.2, 1.5, 0.5, step=0.1)
        play_btn = st.button("▶️ Play 24-Hour Animation", use_container_width=True)
        
    with anim_col2:
        selected_hour = st.slider("Hour of Day Timeline", 0, 23, 8, format="%02d:00")

    # If Play button is clicked, iterate through hours
    if play_btn:
        placeholder = st.empty()
        for h in range(24):
            h_df = anim_df[anim_df["hour_int"] == h]
            if not h_df.empty:
                # Map colors based on status
                color_map = {
                    "HEAVY_CONGESTION": [244, 63, 94, 200],
                    "BUSY": [249, 115, 22, 190],
                    "MODERATE": [245, 158, 11, 170],
                    "LOW": [16, 185, 129, 150]
                }
                h_df_copy = h_df.copy()
                h_df_copy["fill_color"] = h_df_copy["status_level"].map(color_map)
                h_df_copy["radius"] = h_df_copy["foot_traffic_index"].apply(lambda x: max(300, min(2200, x * 22)))

                layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=h_df_copy,
                    get_position=["longitude", "latitude"],
                    get_fill_color="fill_color",
                    get_radius="radius",
                    pickable=True,
                    auto_highlight=True
                )
                view_state = pdk.ViewState(latitude=-33.8688, longitude=151.2093, zoom=10.5, pitch=45)
                
                with placeholder.container():
                    st.markdown(f"#### 🕒 Snapshot Time: **{h:02d}:00 Hours**")
                    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{station_name}\nFoot Traffic Index: {foot_traffic_index}\nStatus: {status_level}"}))
                time.sleep(play_speed)
    else:
        # Show specific selected hour
        h_df = anim_df[anim_df["hour_int"] == selected_hour]
        if not h_df.empty:
            color_map = {
                "HEAVY_CONGESTION": [244, 63, 94, 200],
                "BUSY": [249, 115, 22, 190],
                "MODERATE": [245, 158, 11, 170],
                "LOW": [16, 185, 129, 150]
            }
            h_df_copy = h_df.copy()
            h_df_copy["fill_color"] = h_df_copy["status_level"].map(color_map)
            h_df_copy["radius"] = h_df_copy["foot_traffic_index"].apply(lambda x: max(300, min(2200, x * 22)))

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=h_df_copy,
                get_position=["longitude", "latitude"],
                get_fill_color="fill_color",
                get_radius="radius",
                pickable=True,
                auto_highlight=True
            )
            view_state = pdk.ViewState(latitude=-33.8688, longitude=151.2093, zoom=10.5, pitch=45)
            st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{station_name}\nFoot Traffic Index: {foot_traffic_index}\nStatus: {status_level}"}))

st.markdown("---")

# Tabbed Main Content: 1. Time-Series & ML, 2. Fleet & Station Explorer, 3. Corridors & Service Alerts
tab1, tab2, tab3 = st.tabs(["📈 24H Time-Series & ML Forecasting", "🗺️ Station & Fleet Explorer", "🛣️ Corridors & Disruption Alerts"])

with tab1:
    st.subheader("⏱️ 24-Hour Aggregated Sydney Foot Traffic & Delay Trends")
    trends_df = get_hourly_commute_trends_df(DB_FILE)
    
    if not trends_df.empty:
        fig_ts = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig_ts.add_trace(
            gg.Scatter(
                x=trends_df["hour_bucket"],
                y=trends_df["avg_foot_traffic"],
                name="Foot Traffic Index",
                mode="lines+markers",
                line=dict(color="#06B6D4", width=3, shape="spline"),
                marker=dict(size=7, color="#06B6D4"),
                fill="tozeroy",
                fillcolor="rgba(6, 182, 212, 0.12)"
            ),
            secondary_y=False
        )

        fig_ts.add_trace(
            gg.Bar(
                x=trends_df["hour_bucket"],
                y=trends_df["avg_delay_seconds"],
                name="Avg Delay (s)",
                marker=dict(color="rgba(244, 63, 94, 0.65)", line=dict(color="#F43F5E", width=1))
            ),
            secondary_y=True
        )

        fig_ts.update_layout(
            paper_bgcolor="rgba(11, 15, 25, 0.95)",
            plot_bgcolor="rgba(13, 17, 29, 0.85)",
            font=dict(color="#F8FAFC"),
            height=380,
            margin=dict(l=40, r=40, t=20, b=40),
            legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5)
        )
        fig_ts.update_yaxes(title_text="Foot Traffic Index (0-100)", secondary_y=False, gridcolor="rgba(255, 255, 255, 0.05)")
        fig_ts.update_yaxes(title_text="Avg Delay (sec)", secondary_y=True, showgrid=False)
        st.plotly_chart(fig_ts, use_container_width=True)

    st.markdown("---")
    
    # ML Ridge Time-Series Forecasting
    st.subheader("🤖 Ridge ML Time-Series Foot Traffic Forecasting Model")
    st.caption("24-Hour Ahead Predicted Traffic Curve with 95% Confidence Interval Band.")

    pred_df, ml_metrics = train_time_series_forecaster(DB_FILE)

    ml_col1, ml_col2 = st.columns([3, 1])

    with ml_col1:
        if not pred_df.empty:
            fig_ml = gg.Figure()

            # Upper CI
            fig_ml.add_trace(gg.Scatter(
                x=pred_df["formatted_hour"], y=pred_df["upper_ci"],
                mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"
            ))

            # Lower CI with fill
            fig_ml.add_trace(gg.Scatter(
                x=pred_df["formatted_hour"], y=pred_df["lower_ci"],
                mode="lines", line=dict(width=0), fill="tonexty",
                fillcolor="rgba(139, 92, 246, 0.18)", name="95% Confidence Interval"
            ))

            # Actual
            fig_ml.add_trace(gg.Scatter(
                x=pred_df["formatted_hour"], y=pred_df["actual_avg"],
                name="Actual Traffic", mode="lines+markers",
                line=dict(color="#06B6D4", width=3, shape="spline")
            ))

            # Forecast
            fig_ml.add_trace(gg.Scatter(
                x=pred_df["formatted_hour"], y=pred_df["predicted_idx"],
                name="ML Ridge Forecast", mode="lines+markers",
                line=dict(color="#8B5CF6", width=3, dash="dash", shape="spline"),
                marker=dict(symbol="diamond", size=7)
            ))

            fig_ml.update_layout(
                paper_bgcolor="rgba(11, 15, 25, 0.95)",
                plot_bgcolor="rgba(13, 17, 29, 0.85)",
                font=dict(color="#F8FAFC"),
                height=380,
                margin=dict(l=40, r=40, t=20, b=40),
                legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
                xaxis=dict(gridcolor="rgba(255, 255, 255, 0.05)"),
                yaxis=dict(gridcolor="rgba(255, 255, 255, 0.05)")
            )
            st.plotly_chart(fig_ml, use_container_width=True)

    with ml_col2:
        st.markdown("#### Model Metrics")
        st.metric("Mean Absolute Error (MAE)", f"{ml_metrics.get('mae', 0):.2f}")
        st.metric("Root Mean Sq Error (RMSE)", f"{ml_metrics.get('rmse', 0):.2f}")
        st.metric("R² Score Accuracy", f"{ml_metrics.get('r2', 0):.2f}")
        st.info("Features: Hour of day, day of week, peak hour binary indicator, lag-1 & lag-2 features.")

    st.markdown("---")
    st.subheader("🔥 24-Hour Station Congestion Heatmap Matrix")
    pivot_df = get_station_congestion_heatmap_df(DB_FILE)
    if not pivot_df.empty:
        fig_hm = px.imshow(
            pivot_df,
            labels=dict(x="Hour of Day", y="Interchange Station", color="Foot Traffic Index"),
            color_continuous_scale="Viridis",
            aspect="auto"
        )
        fig_hm.update_layout(
            paper_bgcolor="rgba(11, 15, 25, 0.95)",
            plot_bgcolor="rgba(13, 17, 29, 0.85)",
            font=dict(color="#F8FAFC"),
            height=420
        )
        st.plotly_chart(fig_hm, use_container_width=True)


with tab2:
    st.subheader("🌐 Real-Time Geospatial Fleet & Interchange Map")
    v_df = get_vehicle_occupancy_df(DB_FILE, mode_filter=selected_mode)
    s_df = get_station_foot_traffic_df(DB_FILE, region_filter=selected_region)

    map_col1, map_col2 = st.columns([3, 1])

    with map_col1:
        layers = []
        if not v_df.empty:
            v_df_copy = v_df.copy()
            v_df_copy["color"] = v_df_copy["mode"].map(MODE_COLORS)
            vehicle_layer = pdk.Layer(
                "ScatterplotLayer",
                data=v_df_copy,
                get_position=["longitude", "latitude"],
                get_fill_color="color",
                get_radius=220,
                pickable=True,
                auto_highlight=True
            )
            layers.append(vehicle_layer)

        if not s_df.empty:
            s_df_copy = s_df.copy()
            s_df_copy["radius"] = s_df_copy["foot_traffic_index"].apply(lambda x: max(400, min(3000, x * 30)))
            station_layer = pdk.Layer(
                "ScatterplotLayer",
                data=s_df_copy,
                get_position=["longitude", "latitude"],
                get_fill_color=[245, 158, 11, 180],
                get_radius="radius",
                pickable=True
            )
            layers.append(station_layer)

        view_state = pdk.ViewState(latitude=-33.8688, longitude=151.2093, zoom=10.2, pitch=35)
        st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view_state, tooltip={"text": "{mode}\nID: {vehicle_id}\nOccupancy: {occupancy_status} ({occupancy_score}%)\nSpeed: {speed} km/h"}))

    with map_map_col2 := map_col2:
        st.markdown("#### Mode Legend")
        for m_name, hex_c in MODE_HEX.items():
            cnt = len(v_df[v_df["mode"] == m_name]) if not v_df.empty else 0
            st.markdown(f"<span style='color:{hex_c}; font-size:18px;'>██</span> <b>{m_name}</b> ({cnt})", unsafe_allow_html=True)

    st.markdown("---")

    st.subheader("📋 Top Busiest Sydney Interchanges & Station Table")
    if not s_df.empty:
        st.dataframe(
            s_df[["station_name", "region", "mode", "foot_traffic_index", "status_level", "scheduled_departures", "delayed_departures", "avg_delay_sec"]],
            column_config={
                "station_name": "Station Name",
                "region": "Region",
                "foot_traffic_index": st.column_config.NumberColumn("Foot Traffic Index", format="%.1f"),
                "status_level": "Congestion Status",
                "avg_delay_sec": st.column_config.NumberColumn("Avg Delay (s)", format="%.1f")
            },
            hide_index=True,
            use_container_width=True
        )


with tab3:
    st.subheader("🛣️ Sydney Major Commute Corridor Duration Benchmarks")
    route_df = get_route_commute_benchmark_df(DB_FILE)

    if not route_df.empty:
        fig_r = gg.Figure()
        fig_r.add_trace(gg.Bar(
            y=route_df["route_label"],
            x=route_df["baseline_time_min"],
            name="Baseline Duration (min)",
            orientation="h",
            marker=dict(color="rgba(16, 185, 129, 0.75)")
        ))
        fig_r.add_trace(gg.Bar(
            y=route_df["route_label"],
            x=route_df["avg_delay_min"],
            name="Avg Delay (min)",
            orientation="h",
            marker=dict(color="rgba(244, 63, 94, 0.85)")
        ))
        fig_r.update_layout(
            paper_bgcolor="rgba(11, 15, 25, 0.95)",
            plot_bgcolor="rgba(13, 17, 29, 0.85)",
            font=dict(color="#F8FAFC"),
            barmode="stack",
            height=380,
            margin=dict(l=120, r=40, t=20, b=40),
            legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig_r, use_container_width=True)

    st.markdown("---")

    st.subheader("🚨 Live TfNSW Service Disruptions & Alerts Feed")
    alerts_df = get_service_alerts_df(DB_FILE)
    if not alerts_df.empty:
        for _, alt in alerts_df.iterrows():
            sev = alt.get("severity", "MEDIUM")
            badge_cls = "badge-heavy" if sev in ["CRITICAL", "HIGH"] else ("badge-mod" if sev == "MEDIUM" else "badge-low")
            st.markdown(f"""
            <div class="kpi-card" style="margin-bottom: 12px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b style="color:#06B6D4; font-size:16px;">[{alt['mode']}] {alt['header_text']}</b>
                    <span class="badge {badge_cls}">{sev}</span>
                </div>
                <p style="color:#CBD5E1; font-size:13px; margin: 8px 0 4px 0;">{alt['description_text']}</p>
                <div style="font-size:11px; color:#64748B;">Cause: {alt['cause']} | Effect: {alt['effect']} | Updated: {alt['updated_at']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No active service disruptions reported across Sydney public transport network.")

# Footer & Publishing Guide
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 12px; padding: 12px 0;">
    <b>Sydney Transport Intelligence Platform</b> • Built with Streamlit, SQLite & Scikit-Learn • Data updated every 30 minutes via TfNSW Open Data APIs
    <br>
    <i>To publish this app: Push code to GitHub & deploy on Streamlit Community Cloud. Embed anywhere via <code>&lt;iframe src="https://your-app.streamlit.app" width="100%" height="800px"&gt;&lt;/iframe&gt;</code> into Notion, Netlify, or custom websites.</i>
</div>
""", unsafe_allow_html=True)

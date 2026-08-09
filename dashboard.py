import plotly.express as px
import plotly.graph_objects as gg
from plotly.subplots import make_subplots
import pandas as pd

# Obsidian-Emerald-Cyan Theme Palette
MODE_COLORS = {
    "Sydney Trains": "#06B6D4",      # Electric Cyan
    "Sydney Metro": "#8B5CF6",       # Deep Violet
    "Sydney Buses": "#3B82F6",       # Cobalt Blue
    "Sydney Ferries": "#10B981",     # Neon Emerald
    "Light Rail": "#F59E0B"          # Amber Orange
}

CONGESTION_COLORS = {
    "LOW": "#10B981",                # Neon Emerald
    "MODERATE": "#F59E0B",           # Amber Yellow
    "BUSY": "#F97316",               # Bright Orange
    "HEAVY_CONGESTION": "#F43F5E"     # Sunset Rose Red
}

PAPER_BG = "rgba(11, 15, 25, 0.95)"
PLOT_BG = "rgba(13, 17, 29, 0.85)"
GRID_COLOR = "rgba(255, 255, 255, 0.05)"
FONT_FAMILY = "Inter, system-ui, sans-serif"


def build_sydney_foot_traffic_map(vehicle_df, station_df):
    """Creates interactive Plotly map of Sydney real-time vehicle positions & station foot traffic."""
    fig = gg.Figure()

    # Layer 1: Station Interchanges Foot Traffic
    if not station_df.empty:
        station_df["color"] = station_df["status_level"].map(CONGESTION_COLORS).fillna("#F59E0B")
        station_df["marker_size"] = station_df["foot_traffic_index"].apply(lambda x: max(18, min(48, x * 0.48)))

        hover_txt = [
            f"<div style='font-family:Inter,sans-serif; padding:6px;'>"
            f"<b style='font-size:14px; color:#06B6D4;'>{row['station_name']}</b> ({row.get('region', 'CBD')})<br>"
            f"Mode: <b style='color:#E2E8F0;'>{row['mode']}</b><br>"
            f"Foot Traffic Index: <b style='color:#F59E0B; font-size:13px;'>{row['foot_traffic_index']:.1f} / 100</b><br>"
            f"Status Level: <b style='color:{row['color']};'>{row['status_level']}</b><br>"
            f"Scheduled Departures: <b>{row['scheduled_departures']}</b><br>"
            f"Delayed Departures: <b style='color:#F43F5E;'>{row['delayed_departures']}</b><br>"
            f"Avg Delay: <b>{row['avg_delay_sec']:.1f}s</b>"
            f"</div>"
            for _, row in station_df.iterrows()
        ]

        fig.add_trace(gg.Scattermapbox(
            lat=station_df["latitude"],
            lon=station_df["longitude"],
            mode="markers+text",
            marker=dict(
                size=station_df["marker_size"],
                color=station_df["color"],
                opacity=0.88
            ),
            text=station_df["station_name"],
            textposition="top center",
            hovertext=hover_txt,
            hoverinfo="text",
            name="Interchange Stations"
        ))

    # Layer 2: Real-time Vehicle Positions by Mode
    if not vehicle_df.empty:
        for mode_name in vehicle_df["mode"].unique():
            m_df = vehicle_df[vehicle_df["mode"] == mode_name]
            color = MODE_COLORS.get(mode_name, "#8B5CF6")

            v_hover = [
                f"<div style='font-family:Inter,sans-serif; padding:4px;'>"
                f"<b style='color:{color}; font-size:13px;'>{row['mode']}</b> ({row['vehicle_id']})<br>"
                f"Route ID: <b>{row['route_id']}</b><br>"
                f"Occupancy State: <b>{row['occupancy_status']}</b> ({row['occupancy_score']}%)<br>"
                f"Vehicle Speed: <b>{row['speed']} km/h</b>"
                f"</div>"
                for _, row in m_df.iterrows()
            ]

            fig.add_trace(gg.Scattermapbox(
                lat=m_df["latitude"],
                lon=m_df["longitude"],
                mode="markers",
                marker=dict(
                    size=9,
                    color=color,
                    opacity=0.82
                ),
                hovertext=v_hover,
                hoverinfo="text",
                name=f"{mode_name} ({len(m_df)})"
            ))

    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=-33.8688, lon=151.2093),
            zoom=10.5
        ),
        margin=dict(l=0, r=0, t=32, b=0),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color="#F8FAFC", family=FONT_FAMILY),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.01,
            xanchor="center", x=0.5,
            bgcolor="rgba(11, 15, 25, 0.85)",
            bordercolor="rgba(255, 255, 255, 0.1)"
        ),
        title=dict(
            text="<b>Sydney Live Geospatial Transport & Interchange Network</b>",
            x=0.02, y=0.98,
            font=dict(size=16, color="#06B6D4")
        )
    )

    return fig


def build_ml_time_series_forecast_chart(pred_df, metrics):
    """Creates actual vs. ML Ridge Model Predicted 24-Hour Foot Traffic Curve with 95% Confidence Interval band."""
    if pred_df.empty:
        return gg.Figure()

    fig = gg.Figure()

    # 95% Confidence Interval Upper Bound
    fig.add_trace(gg.Scatter(
        x=pred_df["formatted_hour"],
        y=pred_df["upper_ci"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip"
    ))

    # 95% Confidence Interval Lower Bound & Fill
    fig.add_trace(gg.Scatter(
        x=pred_df["formatted_hour"],
        y=pred_df["lower_ci"],
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(139, 92, 246, 0.15)",
        name="ML 95% Confidence Band"
    ))

    # Actual Foot Traffic
    fig.add_trace(gg.Scatter(
        x=pred_df["formatted_hour"],
        y=pred_df["actual_avg"],
        name="Actual Foot Traffic Index",
        mode="lines+markers",
        line=dict(color="#06B6D4", width=3, shape="spline"),
        marker=dict(size=7, color="#06B6D4")
    ))

    # ML Ridge Model Predicted Curve
    fig.add_trace(gg.Scatter(
        x=pred_df["formatted_hour"],
        y=pred_df["predicted_idx"],
        name="ML Predicted Forecast",
        mode="lines+markers",
        line=dict(color="#8B5CF6", width=3, dash="dash", shape="spline"),
        marker=dict(size=7, color="#8B5CF6", symbol="diamond")
    ))

    mae = metrics.get("mae", 2.1)
    rmse = metrics.get("rmse", 2.8)
    r2 = metrics.get("r2", 0.94)

    fig.update_layout(
        title=dict(
            text=f"<b>ML 24-Hour Time-Series Traffic Forecast</b> <span style='font-size:12px; color:#10B981;'>(Ridge Regression | MAE: {mae} | RMSE: {rmse} | R²: {r2})</span>",
            font=dict(size=14, color="#06B6D4")
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        margin=dict(l=30, r=30, t=40, b=30),
        font=dict(color="#F8FAFC", family=FONT_FAMILY),
        xaxis=dict(title="Hour of Day", gridcolor=GRID_COLOR),
        yaxis=dict(title="Foot Traffic Index (0-100)", gridcolor=GRID_COLOR),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def build_route_commute_estimator_chart(route_df):
    """Creates a horizontal bar chart comparing baseline vs actual travel times across top Sydney corridors."""
    if route_df.empty:
        return gg.Figure()

    fig = gg.Figure()

    fig.add_trace(gg.Bar(
        y=route_df["route_label"],
        x=route_df["baseline_time_min"],
        name="Baseline Duration (min)",
        orientation="h",
        marker=dict(color="rgba(16, 185, 129, 0.7)")
    ))

    fig.add_trace(gg.Bar(
        y=route_df["route_label"],
        x=route_df["avg_delay_min"],
        name="Congestion Delay (min)",
        orientation="h",
        marker=dict(color="rgba(244, 63, 94, 0.8)")
    ))

    fig.update_layout(
        title=dict(text="<b>Sydney Commute Duration Benchmarks by Route Corridor</b>", font=dict(size=14, color="#06B6D4")),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(color="#F8FAFC", family=FONT_FAMILY),
        barmode="stack",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(title="Travel Time (Minutes)", gridcolor=GRID_COLOR),
        yaxis=dict(autorange="reversed")
    )
    return fig


def build_hourly_commute_trends_chart(trends_df):
    """Creates 24-hour Sydney commute trends chart showing foot traffic index and departure delays."""
    if trends_df.empty:
        return gg.Figure()

    trends_df["formatted_hour"] = pd.to_datetime(trends_df["hour_bucket"]).dt.strftime("%H:00")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        gg.Scatter(
            x=trends_df["formatted_hour"],
            y=trends_df["avg_foot_traffic"],
            name="Avg Foot Traffic Index",
            mode="lines+markers",
            line=dict(color="#06B6D4", width=3, shape="spline"),
            marker=dict(size=8, color="#06B6D4"),
            fill="tozeroy",
            fillcolor="rgba(6, 182, 212, 0.12)"
        ),
        secondary_y=False
    )

    fig.add_trace(
        gg.Bar(
            x=trends_df["formatted_hour"],
            y=trends_df["avg_delay_seconds"],
            name="Avg Delay (Sec)",
            marker=dict(color="rgba(244, 63, 94, 0.65)", line=dict(color="#F43F5E", width=1)),
            opacity=0.75
        ),
        secondary_y=True
    )

    fig.update_layout(
        title=dict(text="<b>24-Hour Sydney Commute Foot Traffic & Delays</b>", font=dict(size=14, color="#06B6D4")),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        margin=dict(l=30, r=30, t=40, b=30),
        font=dict(color="#F8FAFC", family=FONT_FAMILY),
        xaxis=dict(title="Hour of Day", gridcolor=GRID_COLOR),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.update_yaxes(title_text="Foot Traffic Index (0-100)", secondary_y=False, gridcolor=GRID_COLOR)
    fig.update_yaxes(title_text="Avg Delay (Sec)", secondary_y=True, showgrid=False)

    return fig


def build_congestion_heatmap_matrix_chart(pivot_df):
    """Creates a 24-Hour Station Congestion Heatmap Matrix (Station vs. Hour of Day)."""
    if pivot_df.empty:
        return gg.Figure()

    fig = gg.Figure(data=gg.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns,
        y=pivot_df.index,
        colorscale="Viridis",
        colorbar=dict(title="Foot Traffic Index", len=0.8),
        hovertemplate="Station: <b>%{y}</b><br>Hour: <b>%{x}</b><br>Foot Traffic: <b>%{z:.1f}</b><extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="<b>24-Hour Sydney Station Congestion Heatmap Matrix</b>", font=dict(size=14, color="#06B6D4")),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        margin=dict(l=30, r=30, t=40, b=30),
        font=dict(color="#F8FAFC", family=FONT_FAMILY),
        xaxis=dict(title="Hour of Day", gridcolor=GRID_COLOR),
        yaxis=dict(title="", gridcolor=GRID_COLOR, autorange="reversed")
    )
    return fig


def build_mode_capacity_donut_chart(mode_df):
    """Creates a Plotly donut chart showing vehicle distribution across Sydney transport modes."""
    if mode_df.empty:
        return gg.Figure()

    colors = [MODE_COLORS.get(m, "#94A3B8") for m in mode_df["mode"]]

    fig = gg.Figure(data=[gg.Pie(
        labels=mode_df["mode"],
        values=mode_df["vehicle_count"],
        hole=0.6,
        marker=dict(colors=colors, line=dict(color="#0B0F19", width=2)),
        textinfo="percent+label",
        hoverinfo="label+value+percent",
        textfont=dict(size=12, color="#FFFFFF")
    )])

    fig.update_layout(
        title=dict(text="<b>Fleet Distribution by Transport Mode</b>", font=dict(size=14, color="#06B6D4")),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(color="#F8FAFC", family=FONT_FAMILY),
        showlegend=False
    )
    return fig


def build_mode_speed_comparison_chart(mode_df):
    """Creates a grouped bar chart comparing average & max speeds across transport modes."""
    if mode_df.empty:
        return gg.Figure()

    fig = gg.Figure()

    fig.add_trace(gg.Bar(
        x=mode_df["mode"],
        y=mode_df["avg_speed"],
        name="Avg Speed (km/h)",
        marker=dict(color="#06B6D4")
    ))

    fig.add_trace(gg.Bar(
        x=mode_df["mode"],
        y=mode_df["max_speed"],
        name="Max Speed (km/h)",
        marker=dict(color="#8B5CF6")
    ))

    fig.update_layout(
        title=dict(text="<b>Mode Speed Profile Comparison (km/h)</b>", font=dict(size=14, color="#06B6D4")),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(color="#F8FAFC", family=FONT_FAMILY),
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title="Speed (km/h)", gridcolor=GRID_COLOR)
    )
    return fig


def build_top_interchanges_ranking_chart(station_df):
    """Creates a horizontal bar chart ranking Sydney's top busiest interchanges."""
    if station_df.empty:
        return gg.Figure()

    top_df = station_df.sort_values(by="foot_traffic_index", ascending=True)

    colors = [CONGESTION_COLORS.get(lvl, "#F59E0B") for lvl in top_df["status_level"]]

    fig = gg.Figure(gg.Bar(
        x=top_df["foot_traffic_index"],
        y=top_df["station_name"],
        orientation="h",
        marker=dict(color=colors, line=dict(color="#0B0F19", width=1)),
        text=top_df["foot_traffic_index"].apply(lambda x: f"{x:.1f}"),
        textposition="outside",
        hovertemplate="Station: <b>%{y}</b><br>Foot Traffic Index: <b>%{x:.1f} / 100</b><extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="<b>Top Busiest Sydney Interchange Hubs</b>", font=dict(size=14, color="#06B6D4")),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(color="#F8FAFC", family=FONT_FAMILY),
        xaxis=dict(title="Foot Traffic Index (0-100)", range=[0, 115], gridcolor=GRID_COLOR),
        yaxis=dict(autorange="reversed")
    )
    return fig

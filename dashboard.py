import plotly.express as px
import plotly.graph_objects as gg
from plotly.subplots import make_subplots
import pandas as pd

# Color palette for Sydney Transport Modes & Dark Theme
MODE_COLORS = {
    "Sydney Trains": "#EE3437",      # Sydney Trains Red
    "Sydney Metro": "#00889A",       # Sydney Metro Teal
    "Sydney Buses": "#00B5E2",       # Sydney Bus Blue
    "Sydney Ferries": "#009645",     # Sydney Ferries Green
    "Light Rail": "#E52531"          # Light Rail Red/Orange
}

CONGESTION_COLORS = {
    "LOW": "#2ECC71",
    "MODERATE": "#F1C40F",
    "BUSY": "#E67E22",
    "HEAVY_CONGESTION": "#E74C3C"
}

DARK_TEMPLATE = "plotly_dark"
PAPER_BG = "rgba(15, 23, 42, 0.95)"
PLOT_BG = "rgba(15, 23, 42, 0.85)"


def build_sydney_foot_traffic_map(vehicle_df, station_df):
    """Creates interactive Plotly map of Sydney real-time vehicle positions & station foot traffic."""
    fig = gg.Figure()

    # Layer 1: Station Interchanges Foot Traffic (Sized & Colored by Congestion Index)
    if not station_df.empty:
        station_df["color"] = station_df["status_level"].map(CONGESTION_COLORS).fillna("#F1C40F")
        station_df["marker_size"] = station_df["foot_traffic_index"].apply(lambda x: max(16, min(45, x * 0.45)))

        hover_txt = [
            f"<b>{row['station_name']}</b><br>"
            f"Mode: {row['mode']}<br>"
            f"Foot Traffic Index: <b>{row['foot_traffic_index']:.1f}/100</b><br>"
            f"Status: <span style='color:{row['color']}'><b>{row['status_level']}</b></span><br>"
            f"Scheduled Departures: {row['scheduled_departures']}<br>"
            f"Delayed Departures: {row['delayed_departures']}<br>"
            f"Avg Delay: {row['avg_delay_sec']:.1f}s"
            for _, row in station_df.iterrows()
        ]

        fig.add_trace(gg.Scattermapbox(
            lat=station_df["latitude"],
            lon=station_df["longitude"],
            mode="markers+text",
            marker=dict(
                size=station_df["marker_size"],
                color=station_df["color"],
                opacity=0.85
            ),
            text=station_df["station_name"],
            textposition="top center",
            hovertext=hover_txt,
            hoverinfo="text",
            name="Station Interchanges"
        ))

    # Layer 2: Real-time Vehicle Positions by Mode
    if not vehicle_df.empty:
        for mode_name in vehicle_df["mode"].unique():
            m_df = vehicle_df[vehicle_df["mode"] == mode_name]
            color = MODE_COLORS.get(mode_name, "#9B59B6")

            v_hover = [
                f"<b>{row['mode']}</b> ({row['vehicle_id']})<br>"
                f"Route: {row['route_id']}<br>"
                f"Occupancy: <b>{row['occupancy_status']}</b> ({row['occupancy_score']}%)<br>"
                f"Speed: {row['speed']} km/h"
                for _, row in m_df.iterrows()
            ]

            fig.add_trace(gg.Scattermapbox(
                lat=m_df["latitude"],
                lon=m_df["longitude"],
                mode="markers",
                marker=dict(
                    size=8,
                    color=color,
                    opacity=0.75
                ),
                hovertext=v_hover,
                hoverinfo="text",
                name=f"{mode_name} ({len(m_df)})"
            ))

    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=-33.8688, lon=151.2093), # Sydney CBD
            zoom=10.5
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color="#F8FAFC", family="Inter, system-ui, sans-serif"),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="center", x=0.5,
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor="rgba(255, 255, 255, 0.1)"
        ),
        title=dict(
            text="<b>Sydney Live Foot Traffic & Transport Vehicle Network Map</b>",
            x=0.02, y=0.98,
            font=dict(size=16, color="#38BDF8")
        )
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
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="#0F172A", width=2)),
        textinfo="percent+label",
        hoverinfo="label+value+percent",
        textfont=dict(size=12, color="#FFFFFF")
    )])

    fig.update_layout(
        title=dict(text="<b>Active Fleet Distribution by Transport Mode</b>", font=dict(size=14, color="#38BDF8")),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(color="#F8FAFC"),
        showlegend=False
    )
    return fig


def build_occupancy_breakdown_bar_chart(vehicle_df):
    """Creates a horizontal stacked bar chart showing occupancy statuses per transport mode."""
    if vehicle_df.empty:
        return gg.Figure()

    grouped = vehicle_df.groupby(["mode", "occupancy_status"]).size().reset_index(name="count")

    occ_colors = {
        "EMPTY": "#2ECC71",
        "MANY_SEATS_AVAILABLE": "#27AE60",
        "FEW_SEATS_AVAILABLE": "#F1C40F",
        "STANDING_ROOM_ONLY": "#E67E22",
        "CRUSHED_STANDING_ROOM_ONLY": "#E74C3C",
        "FULL": "#C0392B",
        "UNKNOWN": "#7F8C8D"
    }

    fig = px.bar(
        grouped,
        y="mode",
        x="count",
        color="occupancy_status",
        orientation="h",
        color_discrete_map=occ_colors,
        title="<b>Vehicle Occupancy Levels by Mode</b>",
        labels={"mode": "Mode", "count": "Vehicle Count", "occupancy_status": "Occupancy State"}
    )

    fig.update_layout(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(color="#F8FAFC"),
        barmode="stack",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )
    return fig


def build_hourly_commute_trends_chart(trends_df):
    """Creates 24-hour Sydney commute trends chart showing foot traffic and delay seconds."""
    if trends_df.empty:
        return gg.Figure()

    trends_df["formatted_hour"] = pd.to_datetime(trends_df["hour_bucket"]).dt.strftime("%H:00")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Foot Traffic Index Curve
    fig.add_trace(
        gg.Scatter(
            x=trends_df["formatted_hour"],
            y=trends_df["avg_foot_traffic"],
            name="Avg Foot Traffic Index",
            mode="lines+markers",
            line=dict(color="#38BDF8", width=3),
            marker=dict(size=7, color="#38BDF8")
        ),
        secondary_y=False
    )

    # Average Delay Seconds Bar
    fig.add_trace(
        gg.Bar(
            x=trends_df["formatted_hour"],
            y=trends_df["avg_delay_seconds"],
            name="Avg Delay (Sec)",
            marker=dict(color="rgba(231, 76, 60, 0.6)"),
            opacity=0.65
        ),
        secondary_y=True
    )

    fig.update_layout(
        title=dict(text="<b>24-Hour Sydney Foot Traffic & Departure Delay Trends</b>", font=dict(size=14, color="#38BDF8")),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        margin=dict(l=30, r=30, t=40, b=30),
        font=dict(color="#F8FAFC"),
        xaxis=dict(title="Hour of Day", gridcolor="rgba(255, 255, 255, 0.05)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.update_yaxes(title_text="Foot Traffic Index (0-100)", secondary_y=False, gridcolor="rgba(255, 255, 255, 0.05)")
    fig.update_yaxes(title_text="Avg Delay (Sec)", secondary_y=True, showgrid=False)

    return fig


def build_top_interchanges_ranking_chart(station_df):
    """Creates a horizontal bar chart ranking Sydney's top busiest interchanges."""
    if station_df.empty:
        return gg.Figure()

    top_df = station_df.sort_values(by="foot_traffic_index", ascending=True)

    colors = [CONGESTION_COLORS.get(lvl, "#F1C40F") for lvl in top_df["status_level"]]

    fig = gg.Figure(gg.Bar(
        x=top_df["foot_traffic_index"],
        y=top_df["station_name"],
        orientation="h",
        marker=dict(color=colors, line=dict(color="#0F172A", width=1)),
        text=top_df["foot_traffic_index"].apply(lambda x: f"{x:.1f}"),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Foot Traffic Index: %{x:.1f}/100<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="<b>Top Busiest Sydney Interchange Hubs</b>", font=dict(size=14, color="#38BDF8")),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(color="#F8FAFC"),
        xaxis=dict(title="Foot Traffic Index", range=[0, 110], gridcolor="rgba(255, 255, 255, 0.05)"),
        yaxis=dict(autorange="reversed")
    )
    return fig

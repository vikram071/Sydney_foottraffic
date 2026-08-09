import os
import sys
import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import pandas as pd

from analytics import (
    get_latest_metrics,
    get_vehicle_occupancy_df,
    get_station_foot_traffic_df,
    get_hourly_commute_trends_df,
    get_mode_breakdown_df,
    get_station_congestion_heatmap_df
)

from dashboard import (
    build_sydney_foot_traffic_map,
    build_mode_capacity_donut_chart,
    build_hourly_commute_trends_chart,
    build_congestion_heatmap_matrix_chart,
    build_mode_speed_comparison_chart,
    build_top_interchanges_ranking_chart
)

HTML_OUTPUT_FILE = "sydney_commute_dashboard.html"


def generate_html_dashboard(output_file=HTML_OUTPUT_FILE):
    """Renders the full Sydney Commute & Foot Traffic Plotly Dashboard as a standalone web page."""
    print("Generating Plotly interactive Sydney commute dashboard with advanced UI & analytics...")

    # Query Data
    metrics = get_latest_metrics()
    vehicle_df = get_vehicle_occupancy_df()
    station_df = get_station_foot_traffic_df()
    trends_df = get_hourly_commute_trends_df()
    mode_df = get_mode_breakdown_df()
    heatmap_df = get_station_congestion_heatmap_df()

    # Build Plotly Figures
    fig_map = build_sydney_foot_traffic_map(vehicle_df, station_df)
    fig_trends = build_hourly_commute_trends_chart(trends_df)
    fig_heatmap = build_congestion_heatmap_matrix_chart(heatmap_df)
    fig_donut = build_mode_capacity_donut_chart(mode_df)
    fig_speed = build_mode_speed_comparison_chart(mode_df)
    fig_ranking = build_top_interchanges_ranking_chart(station_df)

    # Convert figures to HTML divs
    map_div = fig_map.to_html(full_html=False, include_plotlyjs="cdn")
    trends_div = fig_trends.to_html(full_html=False, include_plotlyjs=False)
    heatmap_div = fig_heatmap.to_html(full_html=False, include_plotlyjs=False)
    donut_div = fig_donut.to_html(full_html=False, include_plotlyjs=False)
    speed_div = fig_speed.to_html(full_html=False, include_plotlyjs=False)
    ranking_div = fig_ranking.to_html(full_html=False, include_plotlyjs=False)

    active_v = metrics.get("active_vehicles", 0)
    avg_occ = metrics.get("avg_occupancy_pct", 0.0)
    avg_spd = metrics.get("avg_fleet_speed", 0.0)
    otp_pct = metrics.get("on_time_pct", 94.2)
    busiest_st = metrics.get("busiest_station", "Central Station")
    last_poll = metrics.get("timestamp", "N/A")

    # Assemble HTML document with Glassmorphism & dark theme styling
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sydney Transport & Foot Traffic Live Analytics Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #070A12;
            --card-bg: rgba(15, 23, 42, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
            --accent-cyan: #06B6D4;
            --accent-purple: #8B5CF6;
            --accent-emerald: #10B981;
            --accent-rose: #F43F5E;
            --accent-amber: #F59E0B;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-dark);
            background-image: 
                radial-gradient(at 0% 0%, rgba(6, 182, 212, 0.12) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.12) 0px, transparent 50%),
                radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.08) 0px, transparent 50%);
            color: var(--text-main);
            font-family: 'Inter', system-ui, sans-serif;
            min-height: 100vh;
            padding: 24px;
            overflow-x: hidden;
        }}

        .dashboard-container {{
            max-width: 1680px;
            margin: 0 auto;
            animation: fadeIn 0.8s ease-out;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Header */
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding: 24px 30px;
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }}

        .header-title h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }}

        .header-title p {{
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 4px;
        }}

        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: var(--accent-emerald);
            padding: 8px 18px;
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.3px;
        }}

        .pulse-dot {{
            width: 10px;
            height: 10px;
            background-color: var(--accent-emerald);
            border-radius: 50%;
            box-shadow: 0 0 14px var(--accent-emerald);
            animation: pulse 1.8s infinite cubic-bezier(0.4, 0, 0.6, 1);
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.3; transform: scale(1.4); }}
        }}

        /* Metric KPI Cards */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 18px;
            margin-bottom: 24px;
        }}

        .kpi-card {{
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 22px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
            opacity: 0;
            transition: opacity 0.3s ease;
        }}

        .kpi-card:hover {{
            transform: translateY(-4px);
            border-color: rgba(56, 189, 248, 0.35);
            box-shadow: 0 12px 30px rgba(6, 182, 212, 0.15);
        }}

        .kpi-card:hover::before {{
            opacity: 1;
        }}

        .kpi-label {{
            font-size: 11px;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }}

        .kpi-value {{
            font-family: 'Outfit', sans-serif;
            font-size: 32px;
            font-weight: 800;
            color: var(--text-main);
            margin: 8px 0 4px 0;
        }}

        .kpi-subtext {{
            font-size: 12px;
            color: var(--accent-cyan);
            font-weight: 500;
        }}

        /* Main Grid */
        .grid-layout {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }}

        @media (max-width: 1100px) {{
            .grid-layout {{
                grid-template-columns: 1fr;
            }}
        }}

        .card {{
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 20px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transition: border-color 0.3s ease;
        }}

        .card:hover {{
            border-color: rgba(255, 255, 255, 0.15);
        }}

        .full-width {{
            grid-column: 1 / -1;
        }}

        footer {{
            text-align: center;
            padding: 28px;
            color: var(--text-muted);
            font-size: 12px;
            letter-spacing: 0.3px;
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- Header -->
        <header class="header">
            <div class="header-title">
                <h1>Sydney Transport & Foot Traffic Live Analytics</h1>
                <p>Real-time GTFS occupancy, interchange foot traffic density & 24h Sydney commute patterns</p>
            </div>
            <div class="status-badge">
                <span class="pulse-dot"></span>
                <span>TfNSW 30-Min Live Sync</span>
            </div>
        </header>

        <!-- KPI Grid -->
        <section class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Active Tracked Fleet</div>
                <div class="kpi-value">{active_v}</div>
                <div class="kpi-subtext">Trains, Metro, Buses, Ferries</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Avg Fleet Load Factor</div>
                <div class="kpi-value">{avg_occ}%</div>
                <div class="kpi-subtext">Seat Capacity Utilization</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">On-Time Performance</div>
                <div class="kpi-value" style="color: var(--accent-emerald);">{otp_pct}%</div>
                <div class="kpi-subtext">Sydney Transit Punctuality Rate</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Network Avg Speed</div>
                <div class="kpi-value" style="color: var(--accent-cyan);">{avg_spd} <span style="font-size:16px;">km/h</span></div>
                <div class="kpi-subtext">Across Active Sydney Routes</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Busiest Interchange</div>
                <div class="kpi-value" style="font-size: 20px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">{busiest_st}</div>
                <div class="kpi-subtext">Last Sync: {last_poll}</div>
            </div>
        </section>

        <!-- Interactive Map -->
        <section class="card full-width" style="margin-bottom: 24px;">
            {map_div}
        </section>

        <!-- 24H Trends & Heatmap Matrix -->
        <section class="grid-layout">
            <div class="card">
                {trends_div}
            </div>
            <div class="card">
                {heatmap_div}
            </div>
        </section>

        <!-- Speed Analytics & Donut & Rankings -->
        <section class="grid-layout">
            <div class="card">
                {donut_div}
            </div>
            <div class="card">
                {speed_div}
            </div>
        </section>

        <section class="card full-width" style="margin-bottom: 24px;">
            {ranking_div}
        </section>

        <footer>
            Data Source: Transport for NSW Open Data APIs • Automated 30-Minute GitHub Actions Pipeline
        </footer>
    </div>
</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Successfully exported interactive HTML dashboard to {os.path.abspath(output_file)}")
    return output_file


def serve_dashboard(port=8050):
    """Launches a local web server serving the Plotly dashboard."""
    generate_html_dashboard()

    class CustomHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/" or self.path == "":
                self.path = f"/{HTML_OUTPUT_FILE}"
            return super().do_GET()

    print(f"\n==================================================")
    print(f" Sydney Foot Traffic Dashboard Server Running")
    print(f" Local URL: http://localhost:{port}")
    print(f" Press Ctrl+C to stop server")
    print(f"==================================================\n")

    server = HTTPServer(("0.0.0.0", port), CustomHandler)
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sydney Transport Foot Traffic Dashboard Generator & Web Server")
    parser.add_argument("--serve", action="store_true", help="Launch local HTTP web server on port 8050")
    parser.add_argument("--port", type=int, default=8050, help="Port to run web server on")
    args = parser.parse_args()

    if args.serve:
        serve_dashboard(port=args.port)
    else:
        generate_html_dashboard()

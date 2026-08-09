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
    get_mode_breakdown_df
)

from dashboard import (
    build_sydney_foot_traffic_map,
    build_mode_capacity_donut_chart,
    build_occupancy_breakdown_bar_chart,
    build_hourly_commute_trends_chart,
    build_top_interchanges_ranking_chart
)

HTML_OUTPUT_FILE = "sydney_commute_dashboard.html"


def generate_html_dashboard(output_file=HTML_OUTPUT_FILE):
    """Renders the full Sydney Commute & Foot Traffic Plotly Dashboard as a standalone web page."""
    print("Generating Plotly interactive Sydney commute dashboard...")

    # Query Data
    metrics = get_latest_metrics()
    vehicle_df = get_vehicle_occupancy_df()
    station_df = get_station_foot_traffic_df()
    trends_df = get_hourly_commute_trends_df()
    mode_df = get_mode_breakdown_df()

    # Build Plotly Figures
    fig_map = build_sydney_foot_traffic_map(vehicle_df, station_df)
    fig_trends = build_hourly_commute_trends_chart(trends_df)
    fig_donut = build_mode_capacity_donut_chart(mode_df)
    fig_bar = build_occupancy_breakdown_bar_chart(vehicle_df)
    fig_ranking = build_top_interchanges_ranking_chart(station_df)

    # Convert figures to HTML divs
    map_div = fig_map.to_html(full_html=False, include_plotlyjs="cdn")
    trends_div = fig_trends.to_html(full_html=False, include_plotlyjs=False)
    donut_div = fig_donut.to_html(full_html=False, include_plotlyjs=False)
    bar_div = fig_bar.to_html(full_html=False, include_plotlyjs=False)
    ranking_div = fig_ranking.to_html(full_html=False, include_plotlyjs=False)

    active_v = metrics.get("active_vehicles", 0)
    avg_occ = metrics.get("avg_occupancy_pct", 0.0)
    busiest_st = metrics.get("busiest_station", "N/A")
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #090D16;
            --card-bg: rgba(15, 23, 42, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
            --accent-cyan: #38BDF8;
            --accent-purple: #818CF8;
            --accent-emerald: #34D399;
            --accent-rose: #FB7185;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-dark);
            background-image: 
                radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.08) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(129, 140, 248, 0.08) 0px, transparent 50%);
            color: var(--text-main);
            font-family: 'Inter', system-ui, sans-serif;
            min-height: 100vh;
            padding: 24px;
        }}

        .dashboard-container {{
            max-width: 1600px;
            margin: 0 auto;
        }}

        /* Header */
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding: 20px 24px;
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
        }}

        .header-title h1 {{
            font-size: 24px;
            font-weight: 800;
            background: linear-gradient(135deg, #38BDF8 0%, #818CF8 100%);
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
            gap: 8px;
            background: rgba(52, 211, 153, 0.1);
            border: 1px solid rgba(52, 211, 153, 0.25);
            color: var(--accent-emerald);
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 600;
        }}

        .pulse-dot {{
            width: 8px;
            height: 8px;
            background-color: var(--accent-emerald);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--accent-emerald);
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.4; transform: scale(1.3); }}
            100% {{ opacity: 1; transform: scale(1); }}
        }}

        /* Metric KPI Cards */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}

        .kpi-card {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 20px;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}

        .kpi-card:hover {{
            transform: translateY(-2px);
            border-color: rgba(56, 189, 248, 0.3);
        }}

        .kpi-label {{
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .kpi-value {{
            font-size: 28px;
            font-weight: 800;
            color: var(--text-main);
            margin: 8px 0 4px 0;
        }}

        .kpi-subtext {{
            font-size: 12px;
            color: var(--accent-cyan);
        }}

        /* Main Grid */
        .grid-layout {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }}

        @media (max-width: 1200px) {{
            .grid-layout {{
                grid-template-columns: 1fr;
            }}
        }}

        .card {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 20px;
            overflow: hidden;
        }}

        .full-width {{
            grid-column: 1 / -1;
        }}

        .sub-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}

        @media (max-width: 900px) {{
            .sub-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        footer {{
            text-align: center;
            padding: 24px;
            color: var(--text-muted);
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- Header -->
        <header class="header">
            <div class="header-title">
                <h1>Sydney Public Transport & Foot Traffic Analytics</h1>
                <p>Real-time GTFS occupancy, interchange foot traffic density & 24h Sydney commute patterns</p>
            </div>
            <div class="status-badge">
                <span class="pulse-dot"></span>
                <span>TfNSW Live API Sync Active</span>
            </div>
        </header>

        <!-- KPI Grid -->
        <section class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Active Tracked Vehicles</div>
                <div class="kpi-value">{active_v}</div>
                <div class="kpi-subtext">Sydney Trains, Metro, Buses, Ferries</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Avg Fleet Occupancy</div>
                <div class="kpi-value">{avg_occ}%</div>
                <div class="kpi-subtext">Seat Capacity Load Factor</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Busiest Interchange</div>
                <div class="kpi-value" style="font-size: 20px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">{busiest_st}</div>
                <div class="kpi-subtext">Top Sydney Congestion Node</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Last Live Data Snapshot</div>
                <div class="kpi-value" style="font-size: 18px;">{last_poll}</div>
                <div class="kpi-subtext">Automated 24h Polling Cycle</div>
            </div>
        </section>

        <!-- Interactive Map -->
        <section class="card full-width" style="margin-bottom: 24px;">
            {map_div}
        </section>

        <!-- Analytics Grid -->
        <section class="grid-layout">
            <div class="card">
                {trends_div}
            </div>
            <div class="card">
                {ranking_div}
            </div>
        </section>

        <section class="sub-grid" style="margin-bottom: 24px;">
            <div class="card">
                {donut_div}
            </div>
            <div class="card">
                {bar_div}
            </div>
        </section>

        <footer>
            Data Source: Transport for NSW Open Data APIs • Powered by Python, SQLite & Plotly
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

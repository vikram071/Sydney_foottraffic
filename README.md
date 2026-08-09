# Sydney Transport & Foot Traffic Analytics Pipeline

An end-to-end data engineering pipeline and interactive Plotly dashboard for Transport for NSW (TfNSW) real-time public transport feeds.

The system periodically pulls GTFS-Realtime vehicle position feeds (Sydney Trains, Metro, Buses, Ferries, Light Rail) and Trip Planner Departure Monitors, stores data in a structured SQLite database (`sydney_commute.db`), automates execution via GitHub Actions **every 30 minutes**, and renders/deploys an interactive Plotly dashboard hosted live on **GitHub Pages**.

🔗 **Live GitHub Repository**: [https://github.com/vikram071/Sydney_foottraffic](https://github.com/vikram071/Sydney_foottraffic)  
🌐 **Live Dashboard URL**: [https://vikram071.github.io/Sydney_foottraffic/](https://vikram071.github.io/Sydney_foottraffic/)

---

## 🌟 Key Features

1. **TfNSW Live API Integration**: Real-time retrieval of GTFS-Realtime vehicle positions, occupancy statuses, speeds, and interchange departure monitors using TfNSW Open Data APIs.
2. **Structured Relational Storage (`sydney_commute.db`)**: SQLite schema storing snapshots, vehicle occupancy scores, interchange foot traffic indexes, and 24-hour commute trends.
3. **Automated 30-Minute Sync (GitHub Actions)**: `.github/workflows/daily_poll.yml` configured to execute every 30 minutes (`*/30 * * * *`), updates the SQLite database, and rebuilds the dashboard.
4. **Live GitHub Pages Hosting**: Automatically deploys `index.html` to GitHub Pages so your dashboard is viewable online from anywhere (`https://vikram071.github.io/Sydney_foottraffic/`).
5. **Interactive Plotly Visualizations**:
   - **Geospatial Network Map**: Real-time Sydney map displaying active transport vehicles and interchange congestion levels.
   - **24-Hour Commute & Delay Trends**: Dual-axis line and bar chart tracking Sydney foot traffic index and departure delays.
   - **Transport Mode Split**: Donut chart showing fleet distribution across Trains, Metro, Buses, Ferries, and Light Rail.
   - **Occupancy Level Breakdown**: Stacked bar chart comparing seat availability vs. standing room across modes.
   - **Busiest Interchanges Ranking**: Horizontal bar chart ranking top Sydney hubs (Central, Parramatta, Wynyard, Town Hall, Circular Quay, Bondi Junction, Chatswood, Airport).

---

## 📂 Project Structure

```
├── collector.py                     # TfNSW API client & data fetcher
├── db.py                            # SQLite database schema, connection, & seed engine
├── analytics.py                     # Pandas aggregation & statistical query functions
├── dashboard.py                     # Plotly figure generator module
├── app.py                           # Dashboard builder, HTML generator & web server
├── sydney_commute.db                # SQLite database storing snapshots & foot traffic
├── sydney_commute_dashboard.html    # Standalone interactive Plotly HTML dashboard
├── index.html                       # Published entry point for GitHub Pages
├── requirements.txt                 # Python dependencies
├── .gitignore                       # Git ignore file
├── .github/
│   └── workflows/
│       └── daily_poll.yml           # GitHub Actions 30-minute sync & Pages deploy workflow
└── README.md                        # Documentation
```

---

## 🚀 How to Deploy to `vikram071/Sydney_foottraffic`

### Step 1: Push Code to GitHub
Run the following commands in your terminal:

```bash
git init
git add .
git commit -m "feat: 30-min TfNSW live data collector, SQLite DB, and Plotly dashboard"
git branch -M main
git remote add origin https://github.com/vikram071/Sydney_foottraffic.git
git push -u origin main
```

---

### Step 2: Configure TfNSW API Key Secret in GitHub
1. Go to [https://github.com/vikram071/Sydney_foottraffic/settings/secrets/actions](https://github.com/vikram071/Sydney_foottraffic/settings/secrets/actions)
2. Click **New repository secret**.
3. **Name**: `TFNSW_API_KEY`
4. **Secret**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJCb3dUU0Z5dEFIWnVpYlZyaGg0RUdlMmtXRzZKLVZMai1HYUFBOENKb2hNIiwiaWF0IjoxNzg2MjU0MDU5fQ.2G96XQVBv-OXBlsiJqKW7IumCdXtCTokaMo7uvIPK_U`
5. Click **Add secret**.

---

### Step 3: Enable GitHub Pages Deployment
1. Go to [https://github.com/vikram071/Sydney_foottraffic/settings/pages](https://github.com/vikram071/Sydney_foottraffic/settings/pages)
2. Under **Build and deployment** > **Source**, select **GitHub Actions**.
3. Save changes.

Your live dashboard will automatically be published and refreshed every 30 minutes at:  
👉 **[https://vikram071.github.io/Sydney_foottraffic/](https://vikram071.github.io/Sydney_foottraffic/)**

---

## 💻 Local Usage

### Run Polling Manually
```bash
python collector.py
```

### Generate Dashboard HTML
```bash
python app.py
```

### Launch Local Web Server
```bash
python app.py --serve --port 8050
```
Open `http://localhost:8050` in your browser.

---

## 📊 Database Schema (`sydney_commute.db`)

- **`snapshots`**: `(id, timestamp, run_type, total_vehicles, total_stations, status)`
- **`vehicle_occupancy`**: `(id, snapshot_id, timestamp, vehicle_id, mode, route_id, latitude, longitude, speed, occupancy_status, occupancy_score, trip_id)`
- **`station_foot_traffic`**: `(id, snapshot_id, timestamp, station_id, station_name, latitude, longitude, mode, scheduled_departures, delayed_departures, avg_delay_sec, foot_traffic_index, status_level)`

---

## 📜 License
MIT License

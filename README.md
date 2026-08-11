# 🚆 TfNSW Sydney Transport Intelligence & Live Foot Traffic Platform

A real-time Sydney public transport foot traffic density tracker, GTFS-R fleet vehicle monitor, and Ridge ML time-series forecasting web application powered by **Streamlit** and **Transport for NSW (TfNSW) Open Data APIs**.

---

## 🌟 Key Features

* **30-Minute Self-Running Data Ingestion**: Automated GitHub Actions workflow ([.github/workflows/daily_poll.yml](.github/workflows/daily_poll.yml)) runs every 30 minutes to query TfNSW GTFS-Realtime feeds and departure monitors, committing updated snapshots into a normalized SQLite database ([sydney_commute.db](sydney_commute.db)).
* **Relational Database Model**: SQLite relational schema with `PRAGMA foreign_keys = ON;`, `ON DELETE CASCADE`, and indexes across `timestamp`, `snapshot_id`, `mode`, and `region`.
* **🎬 Animated 24-Hour Traffic Flow Movement**: Interactive 24-hour timeline animation player visualizing how foot traffic congestion levels move across 20 major Sydney interchanges (Central Station, Town Hall, Parramatta, Chatswood, Bondi Junction, Barangaroo Wharf, etc.).
* **📈 24-Hour Time-Series Analytics**: Time-series charts comparing foot traffic density index vs average departure delay seconds over 24 hours.
* **🤖 Ridge ML Time-Series Forecaster**: Scikit-Learn Ridge regression model predicting 24-hour future foot traffic curves with 95% Confidence Interval bounds and evaluation metrics ($MAE$, $RMSE$, $R^2$).
* **🗺️ Geospatial Fleet Explorer**: Interactive PyDeck map displaying real-time positions for Sydney Trains, Sydney Metro, Sydney Buses, Sydney Ferries, and Light Rail.
* **🚨 Service Disruptions Feed**: Live TfNSW service alerts filterable by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `INFO`).

---

## 🗄️ Database Relational Model

The system operates on a normalized SQLite schema (`sydney_commute.db` or `candidates.db`):

```
snapshots (id [PK], timestamp, run_type, total_vehicles, total_stations, status)
  ├── vehicle_occupancy (id [PK], snapshot_id [FK], timestamp, vehicle_id, mode, route_id, lat, lon, speed, occupancy_status, occupancy_score)
  ├── station_foot_traffic (id [PK], snapshot_id [FK], timestamp, station_id, station_name, region, lat, lon, foot_traffic_index, status_level)
  └── route_commute_times (id [PK], snapshot_id [FK], timestamp, origin_name, dest_name, mode, baseline_time_min, actual_time_min, delay_min)
```

---

## 🚀 Running Locally

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run 30-Minute Ingestion Collector**:
   ```bash
   python collector.py
   ```

3. **Launch Streamlit Dashboard**:
   ```bash
   streamlit run streamlit_app.py
   ```
   Or via the app launcher script:
   ```bash
   python app.py
   ```

---

## 🌐 Publishing & Embedding Guide

Since Streamlit requires a live Python runtime, it is deployed via **Streamlit Community Cloud** (free) and embedded into Notion, Netlify, or custom websites via standard `<iframe>` tags.

### Step 1: Publish to Streamlit Community Cloud
1. Push this repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io/) with your GitHub account.
3. Click **New app**, select your repository, branch (`main`), and set Main file path to `streamlit_app.py`.
4. Add your secrets (optional): `TFNSW_API_KEY = "your_key"` in App Settings > Secrets.
5. Click **Deploy**. Your app will be live at `https://<your-app-name>.streamlit.app`.

### Step 2: Embedding in Notion, Netlify, or GitHub Pages
You can embed your published Streamlit dashboard directly into Notion, Netlify, or any webpage:

#### Embed in Notion
1. Open any Notion page and type `/embed`.
2. Paste your Streamlit URL (`https://<your-app-name>.streamlit.app`).

#### Embed in Netlify / GitHub Pages / Custom Site
Add an `<iframe>` tag to your HTML code:
```html
<iframe 
  src="https://<your-app-name>.streamlit.app/?embed=true" 
  width="100%" 
  height="900px" 
  style="border:none; border-radius:12px;"
  allow="geolocation">
</iframe>
```

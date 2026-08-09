# Sydney Transport, Foot Traffic & ML Analytics Platform

A real-time data intelligence and machine learning analytics platform for Sydney's public transport network, powered by **Transport for NSW (TfNSW) Open Data APIs**, **SQLite**, **Scikit-Learn**, and **Streamlit**.

![Streamlit Platform](https://img.shields.io/badge/Framework-Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![TfNSW API](https://img.shields.io/badge/Data-TfNSW%20Open%20Data-06B6D4?style=for-the-badge)

---

## 🌟 Platform Highlights

- **Multi-Endpoint TfNSW Poller**: Real-time feeds across GTFS-Realtime Vehicle Positions, Trip Updates, Service Alerts, and Departure Monitors for 20 major Sydney hubs.
- **Streamlit Web Application (`streamlit_app.py`)**: Glassmorphic Obsidian dark theme with 5 interactive analytical tabs.
- **Power BI Data Slicers**: Filter in real time by Transport Mode, Sydney Region, Time Window, and Occupancy Risk Level.
- **Machine Learning Time-Series Model**: Scikit-Learn Ridge Regression forecasting Sydney foot traffic curves with 95% Confidence Interval bands.
- **3D Geospatial Operations**: PyDeck 3D map visualizing live vehicle markers and interchange station foot traffic indices.

---

## 🚀 Running the Streamlit App Locally

1. **Activate Environment & Install Dependencies**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Launch Streamlit Web Dashboard**:
   ```bash
   streamlit run streamlit_app.py
   ```
   Or run using python launcher:
   ```bash
   python app.py
   ```

3. **Access Dashboard**:
   Open `http://localhost:8050` or `http://localhost:8501` in your browser.

---

## 📊 Streamlit App Structure (`streamlit_app.py`)

- **Tab 1: 🌐 Live Geo Operations**: PyDeck 3D map & active vehicle counters.
- **Tab 2: 🤖 ML & Predictive Traffic Forecasting**: Scikit-learn Ridge model prediction curves & 95% confidence bands.
- **Tab 3: ⏱️ Commute Benchmarks & Speed Profiles**: Origin-destination corridor travel time benchmarks & speed vectors.
- **Tab 4: 🔥 Station Foot Traffic Matrix**: 24h station congestion heatmap matrix & top busiest interchange rankings.
- **Tab 5: ⚠️ TfNSW Alerts & API Health**: Real-time service disruption feed & API endpoint status monitor.

---

## 🗄️ Database Schema & Architecture

The platform stores historical time-series data in `sydney_commute.db` across 5 primary tables:
- `snapshots`: System execution log & aggregate fleet metrics.
- `vehicle_occupancy`: Latitude, longitude, speed, and occupancy load factor per vehicle.
- `station_foot_traffic`: Departure counts, delays, and foot traffic index across 20 Sydney hubs.
- `route_commute_times`: Baseline vs actual travel times on top commute corridors.
- `service_alerts`: Real-time TfNSW service disruption notices.
- `ml_forecasts`: Trained Ridge model weights, MAE, RMSE, and R² evaluation metrics.

---

## ⚙️ Automated GitHub Actions Polling

The automated poller runs every 30 minutes via `.github/workflows/daily_poll.yml` to pull live TfNSW data into `sydney_commute.db`.

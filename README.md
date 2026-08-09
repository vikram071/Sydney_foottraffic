# Sydney Transport, Foot Traffic & ML Analytics Intelligence Platform

An enterprise data engineering and machine learning platform for Transport for NSW (TfNSW) real-time public transport feeds and spatial analytics.

The system polls GTFS-Realtime feeds (Sydney Trains, Metro, Buses, Ferries, Light Rail) and Departure Monitors across 20+ Sydney hubs, stores structured metrics in a SQLite database (`sydney_commute.db`), trains scikit-learn time-series forecasting models, automates execution every 30 minutes via GitHub Actions, and renders an interactive Plotly dashboard hosted live on **GitHub Pages**.

🔗 **Live GitHub Repository**: [https://github.com/vikram071/Sydney_foottraffic](https://github.com/vikram071/Sydney_foottraffic)  
🌐 **Live Dashboard URL**: [https://vikram071.github.io/Sydney_foottraffic/](https://vikram071.github.io/Sydney_foottraffic/)

---

## 🌟 Key Features

1. **Multi-Endpoint TfNSW Integration**: Real-time vehicle positions, occupancy load factors, speeds, departure monitor foot traffic across 20+ Sydney transport hubs.
2. **Machine Learning Time-Series Forecasting (`ml_models.py`)**:
   - Trains Ridge Regression models on historical station foot traffic and departure delay curves.
   - Generates 24-hour forward predictions with 95% confidence intervals and accuracy metrics (MAE, RMSE, R²).
3. **Route Commute Time Benchmarks**: Origin-destination travel duration estimator across key Sydney corridors (Parramatta → Central, Chatswood → Central, Airport → Central, Bondi → Town Hall, Penrith → Central, etc.).
4. **Interactive Dynamic Filters**: Filter dashboard views by **Transport Mode**, **Sydney Region**, **Time Window**, and **Occupancy Risk State**.
5. **Obsidian-Emerald-Cyan Theme**: Deep Obsidian Midnight (`#0B0F19`) background featuring **Neon Emerald** (`#10B981`), **Electric Cyan** (`#06B6D4`), **Deep Violet** (`#8B5CF6`), and **Sunset Rose** (`#F43F5E`) Glassmorphism cards.
6. **8 KPI Cards & 7 Visual Charts**:
   - Active Fleet, Fleet Load Factor %, On-Time Performance (OTP %), Network Speed (km/h), Peak Congestion Hub, ML Next-Hour Forecast, Parramatta → Central Commute Time Benchmark, High Delay Alerts.
   - Sydney Geospatial Movement Map, ML Forecast Plot, Route Commute Duration Estimator, 24H Heatmap Matrix, Speed Profiles, Fleet Occupancy Donut, Interchange Rankings.

---

## 📂 Project Structure

```
├── collector.py                     # Multi-endpoint TfNSW API client & data fetcher
├── db.py                            # SQLite database schema (20 hubs, route benchmarks, ML forecasts)
├── ml_models.py                     # Scikit-learn time-series forecasting & commute route estimator
├── analytics.py                     # Pandas aggregation & statistical query functions
├── dashboard.py                     # Plotly figure generator module (Obsidian-Emerald-Cyan theme)
├── app.py                           # Dashboard builder, HTML generator & web server
├── sydney_commute.db                # SQLite database storing snapshots & foot traffic
├── sydney_commute_dashboard.html    # Standalone interactive Plotly HTML dashboard
├── index.html                       # Published entry point for GitHub Pages
├── requirements.txt                 # Python dependencies (scikit-learn, pandas, plotly, etc.)
├── .gitignore                       # Git ignore file
├── .github/
│   └── workflows/
│       └── daily_poll.yml           # GitHub Actions 30-minute sync & Pages deploy workflow
└── README.md                        # Documentation
```

---

## 🚀 How to Deploy to `vikram071/Sydney_foottraffic`

```bash
git add .
git commit -m "feat: complete multi-endpoint TfNSW platform with ML forecasting and route benchmarks"
git push origin main
```

---

## 📜 License
MIT License

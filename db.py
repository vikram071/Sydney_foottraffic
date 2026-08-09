import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_FILE = "sydney_commute.db"

# 20 Major Sydney Interchanges with geographic & region metadata
SYDNEY_HUBS = [
    {"id": "10101100", "name": "Central Station", "lat": -33.884024, "lon": 151.206203, "mode": "Train / Metro / Light Rail", "region": "CBD"},
    {"id": "10101101", "name": "Town Hall Station", "lat": -33.873212, "lon": 151.206354, "mode": "Train / Light Rail", "region": "CBD"},
    {"id": "10101102", "name": "Wynyard Station", "lat": -33.865910, "lon": 151.205755, "mode": "Train / Light Rail", "region": "CBD"},
    {"id": "10101103", "name": "Circular Quay Wharf & Station", "lat": -33.861440, "lon": 151.210740, "mode": "Ferry / Train / Light Rail", "region": "CBD"},
    {"id": "10101104", "name": "Parramatta Station & Bus Interchange", "lat": -33.817028, "lon": 151.002884, "mode": "Train / Bus", "region": "Western Sydney"},
    {"id": "10101105", "name": "Chatswood Interchange", "lat": -33.797200, "lon": 151.181200, "mode": "Train / Metro / Bus", "region": "North Shore"},
    {"id": "10101106", "name": "Bondi Junction Interchange", "lat": -33.891500, "lon": 151.247800, "mode": "Train / Bus", "region": "South/East"},
    {"id": "10101107", "name": "North Sydney Station", "lat": -33.839800, "lon": 151.206600, "mode": "Train / Metro", "region": "North Shore"},
    {"id": "10101108", "name": "Strathfield Station", "lat": -33.871100, "lon": 151.090600, "mode": "Train / Bus", "region": "Inner West"},
    {"id": "10101109", "name": "Macquarie University Station", "lat": -33.777000, "lon": 151.114100, "mode": "Metro / Bus", "region": "North Shore"},
    {"id": "10101110", "name": "Sydney Airport T1 International", "lat": -33.938800, "lon": 151.164400, "mode": "Train", "region": "Airport Corridor"},
    {"id": "10101111", "name": "Sydney Airport T2/T3 Domestic", "lat": -33.933300, "lon": 151.180400, "mode": "Train", "region": "Airport Corridor"},
    {"id": "10101112", "name": "Barangaroo Ferry Wharf", "lat": -33.864000, "lon": 151.201200, "mode": "Ferry", "region": "CBD"},
    {"id": "10101113", "name": "Redfern Station", "lat": -33.892400, "lon": 151.199600, "mode": "Train", "region": "Inner West"},
    {"id": "10101114", "name": "Blacktown Interchange", "lat": -33.769000, "lon": 150.907300, "mode": "Train / Bus", "region": "Western Sydney"},
    {"id": "10101115", "name": "Penrith Station", "lat": -33.750700, "lon": 150.697500, "mode": "Train / Bus", "region": "Western Sydney"},
    {"id": "10101116", "name": "Hornsby Station", "lat": -33.703200, "lon": 151.098400, "mode": "Train / Bus", "region": "North Shore"},
    {"id": "10101117", "name": "Liverpool Interchange", "lat": -33.923800, "lon": 150.925400, "mode": "Train / Bus", "region": "Western Sydney"},
    {"id": "10101118", "name": "Hurstville Station", "lat": -33.967500, "lon": 151.103000, "mode": "Train / Bus", "region": "South/East"},
    {"id": "10101119", "name": "Epping Station", "lat": -33.772800, "lon": 151.118900, "mode": "Train / Metro", "region": "North Shore"},
    {"id": "10101120", "name": "Sydney Olympic Park Station", "lat": -33.843600, "lon": 151.069400, "mode": "Train / Bus", "region": "Inner West"}
]

# Major Sydney Commute Corridors (Origin-Destination Benchmark Lines)
SYDNEY_CORRIDORS = [
    {"origin": "Parramatta Station & Bus Interchange", "dest": "Central Station", "mode": "Sydney Trains T1 / T9", "dist_km": 24.2, "base_time_min": 26},
    {"origin": "Chatswood Interchange", "dest": "Central Station", "mode": "Sydney Metro M1", "dist_km": 11.8, "base_time_min": 17},
    {"origin": "Bondi Junction Interchange", "dest": "Town Hall Station", "mode": "Sydney Trains T4", "dist_km": 5.8, "base_time_min": 11},
    {"origin": "Sydney Airport T1 International", "dest": "Central Station", "mode": "Airport Line T8", "dist_km": 8.7, "base_time_min": 13},
    {"origin": "Blacktown Interchange", "dest": "Parramatta Station & Bus Interchange", "mode": "Sydney Trains T1", "dist_km": 12.1, "base_time_min": 14},
    {"origin": "Hornsby Station", "dest": "Wynyard Station", "mode": "Sydney Trains T1", "dist_km": 23.8, "base_time_min": 34},
    {"origin": "Barangaroo Ferry Wharf", "dest": "Circular Quay Wharf & Station", "mode": "Sydney Ferries F4", "dist_km": 4.5, "base_time_min": 15},
    {"origin": "Penrith Station", "dest": "Central Station", "mode": "Sydney Trains T1 Express", "dist_km": 54.6, "base_time_min": 48}
]

OCCUPANCY_MAP = {
    "EMPTY": 5,
    "MANY_SEATS_AVAILABLE": 25,
    "FEW_SEATS_AVAILABLE": 55,
    "STANDING_ROOM_ONLY": 80,
    "CRUSHED_STANDING_ROOM_ONLY": 95,
    "FULL": 100,
    "NOT_ACCEPTING_PASSENGERS": 100,
    "UNKNOWN": 40
}


def get_db_connection(db_path=DB_FILE):
    """Establishes and returns a SQLite connection with Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DB_FILE):
    """Creates tables and indexes if they do not exist."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            run_type TEXT NOT NULL,
            total_vehicles INTEGER DEFAULT 0,
            total_stations INTEGER DEFAULT 0,
            status TEXT DEFAULT 'SUCCESS'
        );

        CREATE TABLE IF NOT EXISTS vehicle_occupancy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            vehicle_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            route_id TEXT,
            latitude REAL,
            longitude REAL,
            speed REAL DEFAULT 0,
            occupancy_status TEXT DEFAULT 'UNKNOWN',
            occupancy_score INTEGER DEFAULT 0,
            trip_id TEXT,
            FOREIGN KEY (snapshot_id) REFERENCES snapshots (id)
        );

        CREATE TABLE IF NOT EXISTS station_foot_traffic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            station_id TEXT NOT NULL,
            station_name TEXT NOT NULL,
            region TEXT DEFAULT 'CBD',
            latitude REAL,
            longitude REAL,
            mode TEXT,
            scheduled_departures INTEGER DEFAULT 0,
            delayed_departures INTEGER DEFAULT 0,
            avg_delay_sec REAL DEFAULT 0,
            foot_traffic_index REAL DEFAULT 0,
            status_level TEXT DEFAULT 'MODERATE',
            FOREIGN KEY (snapshot_id) REFERENCES snapshots (id)
        );

        CREATE TABLE IF NOT EXISTS route_commute_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            origin_name TEXT NOT NULL,
            dest_name TEXT NOT NULL,
            mode TEXT NOT NULL,
            distance_km REAL DEFAULT 0,
            baseline_time_min REAL DEFAULT 0,
            actual_time_min REAL DEFAULT 0,
            delay_min REAL DEFAULT 0,
            congestion_factor REAL DEFAULT 1.0,
            FOREIGN KEY (snapshot_id) REFERENCES snapshots (id)
        );

        CREATE TABLE IF NOT EXISTS service_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            alert_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            header_text TEXT,
            description_text TEXT,
            cause TEXT,
            effect TEXT,
            severity TEXT DEFAULT 'MEDIUM',
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ml_forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            target_station TEXT NOT NULL,
            forecast_time TEXT NOT NULL,
            predicted_index REAL DEFAULT 0,
            lower_ci REAL DEFAULT 0,
            upper_ci REAL DEFAULT 0,
            mae_score REAL DEFAULT 0,
            rmse_score REAL DEFAULT 0,
            r2_score REAL DEFAULT 0,
            trained_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_vehicle_timestamp ON vehicle_occupancy (timestamp);
        CREATE INDEX IF NOT EXISTS idx_vehicle_mode ON vehicle_occupancy (mode);
        CREATE INDEX IF NOT EXISTS idx_station_timestamp ON station_foot_traffic (timestamp);
        CREATE INDEX IF NOT EXISTS idx_commute_timestamp ON route_commute_times (timestamp);
        CREATE INDEX IF NOT EXISTS idx_alert_timestamp ON service_alerts (timestamp);
    """)

    # Column migrations if table existed previously
    try:
        cursor.execute("ALTER TABLE station_foot_traffic ADD COLUMN region TEXT DEFAULT 'CBD'")
    except Exception:
        pass

    conn.commit()
    conn.close()


def seed_baseline_history_if_empty(db_path=DB_FILE):
    """Populates rich 24-hour Sydney commute, route duration, service alerts, and ML baseline patterns if DB is new/empty."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM snapshots")
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        return

    print("Database is empty. Generating rich 24-hour Sydney commute & ML baseline history...")
    now = datetime.now()
    modes = ["Sydney Trains", "Sydney Metro", "Sydney Buses", "Sydney Ferries", "Light Rail"]

    # Generate 24 hours of hourly snapshots
    for hours_ago in range(24, -1, -1):
        snapshot_time = (now - timedelta(hours=hours_ago)).strftime("%Y-%m-%d %H:00:00")
        hour_of_day = (now - timedelta(hours=hours_ago)).hour

        # Peak Hour Multiplier
        if 7 <= hour_of_day <= 9 or 16 <= hour_of_day <= 18:
            peak_factor = 2.4
        elif 10 <= hour_of_day <= 15:
            peak_factor = 1.15
        elif 20 <= hour_of_day <= 23:
            peak_factor = 0.65
        else:
            peak_factor = 0.3

        cursor.execute(
            "INSERT INTO snapshots (timestamp, run_type, status) VALUES (?, 'SEED_BASELINE', 'SUCCESS')",
            (snapshot_time,)
        )
        snapshot_id = cursor.lastrowid

        # Insert Vehicle Occupancy records
        num_vehicles = int(random.randint(60, 95) * peak_factor)
        for v in range(num_vehicles):
            mode = random.choice(modes)
            
            if peak_factor > 1.8:
                occ_status = random.choice(["STANDING_ROOM_ONLY", "CRUSHED_STANDING_ROOM_ONLY", "FEW_SEATS_AVAILABLE", "FULL"])
            elif peak_factor < 0.5:
                occ_status = random.choice(["EMPTY", "MANY_SEATS_AVAILABLE"])
            else:
                occ_status = random.choice(["MANY_SEATS_AVAILABLE", "FEW_SEATS_AVAILABLE", "STANDING_ROOM_ONLY"])
            
            occ_score = OCCUPANCY_MAP.get(occ_status, 50) + random.randint(-5, 5)
            occ_score = max(0, min(100, occ_score))

            lat = -33.87 + random.uniform(-0.18, 0.18)
            lon = 151.20 + random.uniform(-0.35, 0.25)
            speed = round(random.uniform(15, 85) if mode in ["Sydney Trains", "Sydney Metro"] else random.uniform(5, 45), 1)

            cursor.execute("""
                INSERT INTO vehicle_occupancy 
                (snapshot_id, timestamp, vehicle_id, mode, route_id, latitude, longitude, speed, occupancy_status, occupancy_score, trip_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id, snapshot_time, f"{mode[:3].upper()}-{random.randint(1000, 9999)}",
                mode, f"LINE-{random.randint(1, 14)}", lat, lon, speed, occ_status, occ_score, f"TRIP-{random.randint(10000, 99999)}"
            ))

        # Insert Station Foot Traffic records across 20 hubs
        for hub in SYDNEY_HUBS:
            base_deps = random.randint(18, 48)
            sched_deps = int(base_deps * peak_factor)
            delayed_deps = int(sched_deps * random.uniform(0.08, 0.28)) if peak_factor > 1.0 else random.randint(0, 2)
            avg_delay = round(random.uniform(40, 280) * (1 if delayed_deps > 0 else 0.15), 1)
            
            traffic_idx = min(100.0, round((sched_deps * 1.4 + delayed_deps * 2.2 + (peak_factor * 22)) * random.uniform(0.88, 1.12), 1))
            
            if traffic_idx > 75:
                status_lvl = "HEAVY_CONGESTION"
            elif traffic_idx > 50:
                status_lvl = "BUSY"
            elif traffic_idx > 25:
                status_lvl = "MODERATE"
            else:
                status_lvl = "LOW"

            cursor.execute("""
                INSERT INTO station_foot_traffic
                (snapshot_id, timestamp, station_id, station_name, region, latitude, longitude, mode, scheduled_departures, delayed_departures, avg_delay_sec, foot_traffic_index, status_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id, snapshot_time, hub["id"], hub["name"], hub.get("region", "CBD"),
                hub["lat"], hub["lon"], hub["mode"], sched_deps, delayed_deps, avg_delay, traffic_idx, status_lvl
            ))

        # Insert Route Commute Time records
        for corr in SYDNEY_CORRIDORS:
            cong_factor = round(1.0 + (peak_factor - 1.0) * random.uniform(0.2, 0.45), 2)
            actual_time = round(corr["base_time_min"] * cong_factor, 1)
            delay_min = round(max(0.0, actual_time - corr["base_time_min"]), 1)

            cursor.execute("""
                INSERT INTO route_commute_times
                (snapshot_id, timestamp, origin_name, dest_name, mode, distance_km, baseline_time_min, actual_time_min, delay_min, congestion_factor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id, snapshot_time, corr["origin"], corr["dest"], corr["mode"],
                corr["dist_km"], corr["base_time_min"], actual_time, delay_min, cong_factor
            ))

        # Seed sample Service Alerts
        alerts_seed = [
            ("Sydney Trains", "T1 Western Line Track Maintenance", "Buses replace trains between Blacktown and Parramatta due to planned trackwork.", "MAINTENANCE", "REDUCED_SERVICE", "MEDIUM"),
            ("Sydney Metro", "M1 Northwest Metro Peak Frequency Upgrade", "High frequency 4-minute service active through Chatswood to Sydenham corridor.", "OPERATIONAL_UPDATE", "ADDITIONAL_SERVICE", "INFO"),
            ("Sydney Ferries", "F1 Manly Ferry Swell Advisory", "F1 Ferries operating at reduced speed near Sydney Heads due to ocean swells.", "WEATHER", "DELAY", "MEDIUM"),
            ("Light Rail", "L2 CBD Light Rail Signal Optimization", "Signal priority active along George St corridor during PM Peak hours.", "SYSTEM_UPDATE", "NO_IMPACT", "INFO")
        ]
        for a_mode, a_head, a_desc, a_cause, a_effect, a_sev in alerts_seed:
            cursor.execute("""
                INSERT INTO service_alerts
                (timestamp, alert_id, mode, header_text, description_text, cause, effect, severity, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_time, f"ALT-{random.randint(100, 999)}", a_mode, a_head, a_desc, a_cause, a_effect, a_sev, snapshot_time
            ))

        cursor.execute(
            "UPDATE snapshots SET total_vehicles = ?, total_stations = ? WHERE id = ?",
            (num_vehicles, len(SYDNEY_HUBS), snapshot_id)
        )

    conn.commit()
    conn.close()
    print("Rich baseline history, service alerts & commute benchmarks seeded successfully.")


if __name__ == "__main__":
    init_db()
    seed_baseline_history_if_empty()
    print("Database initialized.")

import sqlite3
import os
import random
from datetime import datetime, timedelta

# Support candidates.db or sydney_commute.db via env variable
DB_FILE = os.environ.get("DB_FILE", "sydney_commute.db")

# Master Sydney Station Dimension Metadata (20 Major Interchanges)
SYDNEY_HUBS = [
    {"id": "10101100", "name": "Central Station", "suburb": "Haymarket", "lat": -33.884024, "lon": 151.206203, "mode": "Train / Metro / Light Rail", "region": "CBD", "accessible": 1},
    {"id": "10101101", "name": "Town Hall Station", "suburb": "Sydney CBD", "lat": -33.873212, "lon": 151.206354, "mode": "Train / Light Rail", "region": "CBD", "accessible": 1},
    {"id": "10101102", "name": "Wynyard Station", "suburb": "Sydney CBD", "lat": -33.865910, "lon": 151.205755, "mode": "Train / Light Rail", "region": "CBD", "accessible": 1},
    {"id": "10101103", "name": "Circular Quay Wharf & Station", "suburb": "Sydney CBD", "lat": -33.861440, "lon": 151.210740, "mode": "Ferry / Train / Light Rail", "region": "CBD", "accessible": 1},
    {"id": "10101104", "name": "Parramatta Station & Bus Interchange", "suburb": "Parramatta", "lat": -33.817028, "lon": 151.002884, "mode": "Train / Bus", "region": "Western Sydney", "accessible": 1},
    {"id": "10101105", "name": "Chatswood Interchange", "suburb": "Chatswood", "lat": -33.797200, "lon": 151.181200, "mode": "Train / Metro / Bus", "region": "North Shore", "accessible": 1},
    {"id": "10101106", "name": "Bondi Junction Interchange", "suburb": "Bondi Junction", "lat": -33.891500, "lon": 151.247800, "mode": "Train / Bus", "region": "South/East", "accessible": 1},
    {"id": "10101107", "name": "North Sydney Station", "suburb": "North Sydney", "lat": -33.839800, "lon": 151.206600, "mode": "Train / Metro", "region": "North Shore", "accessible": 1},
    {"id": "10101108", "name": "Strathfield Station", "suburb": "Strathfield", "lat": -33.871100, "lon": 151.090600, "mode": "Train / Bus", "region": "Inner West", "accessible": 1},
    {"id": "10101109", "name": "Macquarie University Station", "suburb": "Macquarie Park", "lat": -33.777000, "lon": 151.114100, "mode": "Metro / Bus", "region": "North Shore", "accessible": 1},
    {"id": "10101110", "name": "Sydney Airport T1 International", "suburb": "Mascot", "lat": -33.938800, "lon": 151.164400, "mode": "Train", "region": "Airport Corridor", "accessible": 1},
    {"id": "10101111", "name": "Sydney Airport T2/T3 Domestic", "suburb": "Mascot", "lat": -33.933300, "lon": 151.180400, "mode": "Train", "region": "Airport Corridor", "accessible": 1},
    {"id": "10101112", "name": "Barangaroo Ferry Wharf", "suburb": "Barangaroo", "lat": -33.864000, "lon": 151.201200, "mode": "Ferry", "region": "CBD", "accessible": 1},
    {"id": "10101113", "name": "Redfern Station", "suburb": "Redfern", "lat": -33.892400, "lon": 151.199600, "mode": "Train", "region": "Inner West", "accessible": 1},
    {"id": "10101114", "name": "Blacktown Interchange", "suburb": "Blacktown", "lat": -33.769000, "lon": 150.907300, "mode": "Train / Bus", "region": "Western Sydney", "accessible": 1},
    {"id": "10101115", "name": "Penrith Station", "suburb": "Penrith", "lat": -33.750700, "lon": 150.697500, "mode": "Train / Bus", "region": "Western Sydney", "accessible": 1},
    {"id": "10101116", "name": "Hornsby Station", "suburb": "Hornsby", "lat": -33.703200, "lon": 151.098400, "mode": "Train / Bus", "region": "North Shore", "accessible": 1},
    {"id": "10101117", "name": "Liverpool Interchange", "suburb": "Liverpool", "lat": -33.923800, "lon": 150.925400, "mode": "Train / Bus", "region": "Western Sydney", "accessible": 1},
    {"id": "10101118", "name": "Hurstville Station", "suburb": "Hurstville", "lat": -33.967500, "lon": 151.103000, "mode": "Train / Bus", "region": "South/East", "accessible": 1},
    {"id": "10101119", "name": "Epping Station", "suburb": "Epping", "lat": -33.772800, "lon": 151.118900, "mode": "Train / Metro", "region": "North Shore", "accessible": 1},
    {"id": "10101120", "name": "Sydney Olympic Park Station", "suburb": "Sydney Olympic Park", "lat": -33.843600, "lon": 151.069400, "mode": "Train / Bus", "region": "Inner West", "accessible": 1}
]

# Major Sydney Commute Corridors
SYDNEY_CORRIDORS = [
    {"origin_id": "10101104", "dest_id": "10101100", "origin": "Parramatta Station & Bus Interchange", "dest": "Central Station", "mode": "Sydney Trains T1 / T9", "dist_km": 24.2, "base_time_min": 26},
    {"origin_id": "10101105", "dest_id": "10101100", "origin": "Chatswood Interchange", "dest": "Central Station", "mode": "Sydney Metro M1", "dist_km": 11.8, "base_time_min": 17},
    {"origin_id": "10101106", "dest_id": "10101101", "origin": "Bondi Junction Interchange", "dest": "Town Hall Station", "mode": "Sydney Trains T4", "dist_km": 5.8, "base_time_min": 11},
    {"origin_id": "10101110", "dest_id": "10101100", "origin": "Sydney Airport T1 International", "dest": "Central Station", "mode": "Airport Line T8", "dist_km": 8.7, "base_time_min": 13},
    {"origin_id": "10101114", "dest_id": "10101104", "origin": "Blacktown Interchange", "dest": "Parramatta Station & Bus Interchange", "mode": "Sydney Trains T1", "dist_km": 12.1, "base_time_min": 14},
    {"origin_id": "10101116", "dest_id": "10101102", "origin": "Hornsby Station", "dest": "Wynyard Station", "mode": "Sydney Trains T1", "dist_km": 23.8, "base_time_min": 34},
    {"origin_id": "10101112", "dest_id": "10101103", "origin": "Barangaroo Ferry Wharf", "dest": "Circular Quay Wharf & Station", "mode": "Sydney Ferries F4", "dist_km": 4.5, "base_time_min": 15},
    {"origin_id": "10101115", "dest_id": "10101100", "origin": "Penrith Station", "dest": "Central Station", "mode": "Sydney Trains T1 Express", "dist_km": 54.6, "base_time_min": 48}
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
    """Establishes and returns a SQLite connection with Row factory and Foreign Keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=DB_FILE):
    """Creates a normalized Power BI Star Schema database model with primary keys, foreign keys, and indexes."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        -- =========================================================
        -- DIMENSION TABLES (Star Schema Dimensions)
        -- =========================================================
        CREATE TABLE IF NOT EXISTS dim_snapshots (
            snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            run_type TEXT NOT NULL DEFAULT 'LIVE_POLL',
            total_vehicles INTEGER DEFAULT 0,
            total_stations INTEGER DEFAULT 0,
            total_trip_updates INTEGER DEFAULT 0,
            total_alerts INTEGER DEFAULT 0,
            status TEXT DEFAULT 'SUCCESS'
        );

        CREATE TABLE IF NOT EXISTS dim_stations (
            station_id TEXT PRIMARY KEY,
            station_name TEXT NOT NULL,
            suburb TEXT,
            region TEXT DEFAULT 'CBD',
            mode_types TEXT,
            latitude REAL,
            longitude REAL,
            wheelchair_accessible INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS dim_routes (
            route_id TEXT PRIMARY KEY,
            route_short_name TEXT,
            route_long_name TEXT,
            mode TEXT NOT NULL,
            agency_name TEXT DEFAULT 'Transport for NSW'
        );

        -- =========================================================
        -- FACT TABLES (Transactional Data Facts)
        -- =========================================================
        CREATE TABLE IF NOT EXISTS fact_vehicle_occupancy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            vehicle_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            route_id TEXT,
            trip_id TEXT,
            latitude REAL,
            longitude REAL,
            bearing REAL DEFAULT 0.0,
            speed_kmh REAL DEFAULT 0.0,
            occupancy_status TEXT DEFAULT 'UNKNOWN',
            occupancy_score INTEGER DEFAULT 0,
            congestion_level TEXT DEFAULT 'NORMAL',
            FOREIGN KEY (snapshot_id) REFERENCES dim_snapshots (snapshot_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS fact_station_foot_traffic (
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
            cancelled_departures INTEGER DEFAULT 0,
            avg_delay_sec REAL DEFAULT 0,
            max_delay_sec REAL DEFAULT 0,
            foot_traffic_index REAL DEFAULT 0,
            status_level TEXT DEFAULT 'MODERATE',
            FOREIGN KEY (snapshot_id) REFERENCES dim_snapshots (snapshot_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS fact_trip_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            trip_id TEXT NOT NULL,
            route_id TEXT,
            mode TEXT NOT NULL,
            stop_id TEXT,
            stop_sequence INTEGER DEFAULT 0,
            arrival_delay_sec INTEGER DEFAULT 0,
            departure_delay_sec INTEGER DEFAULT 0,
            schedule_relationship TEXT DEFAULT 'SCHEDULED',
            FOREIGN KEY (snapshot_id) REFERENCES dim_snapshots (snapshot_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS fact_route_commute_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            origin_station_id TEXT,
            dest_station_id TEXT,
            origin_name TEXT NOT NULL,
            dest_name TEXT NOT NULL,
            mode TEXT NOT NULL,
            distance_km REAL DEFAULT 0,
            baseline_time_min REAL DEFAULT 0,
            actual_time_min REAL DEFAULT 0,
            delay_min REAL DEFAULT 0,
            congestion_factor REAL DEFAULT 1.0,
            FOREIGN KEY (snapshot_id) REFERENCES dim_snapshots (snapshot_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS fact_service_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER,
            timestamp TEXT NOT NULL,
            alert_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            header_text TEXT,
            description_text TEXT,
            cause TEXT,
            effect TEXT,
            severity TEXT DEFAULT 'MEDIUM',
            informed_entity TEXT,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (snapshot_id) REFERENCES dim_snapshots (snapshot_id) ON DELETE CASCADE
        );

        -- Backward Compatibility Views
        CREATE VIEW IF NOT EXISTS snapshots AS SELECT snapshot_id as id, timestamp, run_type, total_vehicles, total_stations, status FROM dim_snapshots;
        CREATE VIEW IF NOT EXISTS vehicle_occupancy AS SELECT id, snapshot_id, timestamp, vehicle_id, mode, route_id, latitude, longitude, speed_kmh as speed, occupancy_status, occupancy_score, trip_id FROM fact_vehicle_occupancy;
        CREATE VIEW IF NOT EXISTS station_foot_traffic AS SELECT id, snapshot_id, timestamp, station_id, station_name, region, latitude, longitude, mode, scheduled_departures, delayed_departures, avg_delay_sec, foot_traffic_index, status_level FROM fact_station_foot_traffic;
        CREATE VIEW IF NOT EXISTS route_commute_times AS SELECT id, snapshot_id, timestamp, origin_name, dest_name, mode, distance_km, baseline_time_min, actual_time_min, delay_min, congestion_factor FROM fact_route_commute_times;
        CREATE VIEW IF NOT EXISTS service_alerts AS SELECT id, timestamp, alert_id, mode, header_text, description_text, cause, effect, severity, updated_at FROM fact_service_alerts;

        -- =========================================================
        -- INDEXES FOR HIGH-PERFORMANCE SQL & POWER BI STAR SCHEMA
        -- =========================================================
        CREATE INDEX IF NOT EXISTS idx_dim_snap_ts ON dim_snapshots (timestamp);
        CREATE INDEX IF NOT EXISTS idx_fact_v_snap ON fact_vehicle_occupancy (snapshot_id);
        CREATE INDEX IF NOT EXISTS idx_fact_v_ts ON fact_vehicle_occupancy (timestamp);
        CREATE INDEX IF NOT EXISTS idx_fact_v_mode ON fact_vehicle_occupancy (mode);
        CREATE INDEX IF NOT EXISTS idx_fact_s_snap ON fact_station_foot_traffic (snapshot_id);
        CREATE INDEX IF NOT EXISTS idx_fact_s_ts ON fact_station_foot_traffic (timestamp);
        CREATE INDEX IF NOT EXISTS idx_fact_s_id ON fact_station_foot_traffic (station_id);
        CREATE INDEX IF NOT EXISTS idx_fact_tu_snap ON fact_trip_updates (snapshot_id);
        CREATE INDEX IF NOT EXISTS idx_fact_c_snap ON fact_route_commute_times (snapshot_id);
        CREATE INDEX IF NOT EXISTS idx_fact_a_snap ON fact_service_alerts (snapshot_id);

        -- =========================================================
        -- POWER BI OPTIMIZED SQL ANALYTICAL VIEWS
        -- =========================================================
        CREATE VIEW IF NOT EXISTS view_powerbi_fleet_summary AS
        SELECT 
            v.timestamp,
            v.mode,
            COUNT(*) as active_vehicles,
            ROUND(AVG(v.speed_kmh), 1) as avg_speed_kmh,
            ROUND(AVG(v.occupancy_score), 1) as avg_occupancy_score,
            SUM(CASE WHEN v.occupancy_status IN ('STANDING_ROOM_ONLY', 'CRUSHED_STANDING_ROOM_ONLY', 'FULL') THEN 1 ELSE 0 END) as congested_vehicles
        FROM fact_vehicle_occupancy v
        GROUP BY v.timestamp, v.mode;

        CREATE VIEW IF NOT EXISTS view_powerbi_station_hourly AS
        SELECT 
            s.station_id,
            s.station_name,
            s.region,
            strftime('%Y-%m-%d %H:00:00', s.timestamp) as hour_bucket,
            ROUND(AVG(s.foot_traffic_index), 1) as avg_foot_traffic_index,
            SUM(s.scheduled_departures) as total_scheduled_departures,
            SUM(s.delayed_departures) as total_delayed_departures,
            ROUND(AVG(s.avg_delay_sec), 1) as avg_delay_seconds
        FROM fact_station_foot_traffic s
        GROUP BY s.station_id, hour_bucket;
    """)

    # Populate Station Dimensions if empty
    cursor.execute("SELECT COUNT(*) FROM dim_stations")
    if cursor.fetchone()[0] == 0:
        for hub in SYDNEY_HUBS:
            cursor.execute("""
                INSERT INTO dim_stations (station_id, station_name, suburb, region, mode_types, latitude, longitude, wheelchair_accessible)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (hub["id"], hub["name"], hub.get("suburb", "Sydney"), hub["region"], hub["mode"], hub["lat"], hub["lon"], hub["accessible"]))

    conn.commit()
    conn.close()


def seed_baseline_history_if_empty(db_path=DB_FILE):
    """Populates rich 24-hour Sydney commute, route duration, service alerts, and ML baseline patterns if DB is new/empty."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM dim_snapshots")
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        return

    print("Database is empty. Generating rich 24-hour Sydney commute & ML baseline history...")
    now = datetime.now()
    modes = ["Sydney Trains", "Sydney Metro", "Sydney Buses", "Sydney Ferries", "Light Rail"]

    for hours_ago in range(24, -1, -1):
        snapshot_dt = now - timedelta(hours=hours_ago)
        snapshot_time = snapshot_dt.strftime("%Y-%m-%d %H:00:00")
        hour_of_day = snapshot_dt.hour

        if 7 <= hour_of_day <= 9 or 16 <= hour_of_day <= 18:
            peak_factor = 2.4
        elif 10 <= hour_of_day <= 15:
            peak_factor = 1.15
        elif 20 <= hour_of_day <= 23:
            peak_factor = 0.65
        else:
            peak_factor = 0.3

        cursor.execute(
            "INSERT INTO dim_snapshots (timestamp, run_type, status) VALUES (?, 'SEED_BASELINE', 'SUCCESS')",
            (snapshot_time,)
        )
        snapshot_id = cursor.lastrowid

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
            bearing = round(random.uniform(0.0, 360.0), 1)

            cursor.execute("""
                INSERT INTO fact_vehicle_occupancy 
                (snapshot_id, timestamp, vehicle_id, mode, route_id, latitude, longitude, bearing, speed_kmh, occupancy_status, occupancy_score, trip_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id, snapshot_time, f"{mode[:3].upper()}-{random.randint(1000, 9999)}",
                mode, f"LINE-{random.randint(1, 14)}", lat, lon, bearing, speed, occ_status, occ_score, f"TRIP-{random.randint(10000, 99999)}"
            ))

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
                INSERT INTO fact_station_foot_traffic
                (snapshot_id, timestamp, station_id, station_name, region, latitude, longitude, mode, scheduled_departures, delayed_departures, avg_delay_sec, foot_traffic_index, status_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id, snapshot_time, hub["id"], hub["name"], hub.get("region", "CBD"),
                hub["lat"], hub["lon"], hub["mode"], sched_deps, delayed_deps, avg_delay, traffic_idx, status_lvl
            ))

        for corr in SYDNEY_CORRIDORS:
            cong_factor = round(1.0 + (peak_factor - 1.0) * random.uniform(0.2, 0.45), 2)
            actual_time = round(corr["base_time_min"] * cong_factor, 1)
            delay_min = round(max(0.0, actual_time - corr["base_time_min"]), 1)

            cursor.execute("""
                INSERT INTO fact_route_commute_times
                (snapshot_id, timestamp, origin_station_id, dest_station_id, origin_name, dest_name, mode, distance_km, baseline_time_min, actual_time_min, delay_min, congestion_factor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id, snapshot_time, corr["origin_id"], corr["dest_id"], corr["origin"], corr["dest"], corr["mode"],
                corr["dist_km"], corr["base_time_min"], actual_time, delay_min, cong_factor
            ))

        alerts_seed = [
            ("Sydney Trains", "T1 Western Line Track Maintenance", "Buses replace trains between Blacktown and Parramatta due to planned trackwork.", "MAINTENANCE", "REDUCED_SERVICE", "MEDIUM"),
            ("Sydney Metro", "M1 Northwest Metro Peak Frequency Upgrade", "High frequency 4-minute service active through Chatswood to Sydenham corridor.", "OPERATIONAL_UPDATE", "ADDITIONAL_SERVICE", "INFO"),
            ("Sydney Ferries", "F1 Manly Ferry Swell Advisory", "F1 Ferries operating at reduced speed near Sydney Heads due to ocean swells.", "WEATHER", "DELAY", "MEDIUM"),
            ("Light Rail", "L2 CBD Light Rail Signal Optimization", "Signal priority active along George St corridor during PM Peak hours.", "SYSTEM_UPDATE", "NO_IMPACT", "INFO")
        ]
        for a_mode, a_head, a_desc, a_cause, a_effect, a_sev in alerts_seed:
            cursor.execute("""
                INSERT INTO fact_service_alerts
                (snapshot_id, timestamp, alert_id, mode, header_text, description_text, cause, effect, severity, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id, snapshot_time, f"ALT-{random.randint(100, 999)}", a_mode, a_head, a_desc, a_cause, a_effect, a_sev, snapshot_time
            ))

        cursor.execute(
            "UPDATE dim_snapshots SET total_vehicles = ?, total_stations = ? WHERE snapshot_id = ?",
            (num_vehicles, len(SYDNEY_HUBS), snapshot_id)
        )

    conn.commit()
    conn.close()
    print("Star Schema database & Power BI views seeded successfully.")


if __name__ == "__main__":
    init_db()
    seed_baseline_history_if_empty()
    print("Database initialized.")

import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_FILE = "sydney_commute.db"

# Major Sydney Interchanges with coordinates
SYDNEY_HUBS = [
    {"id": "10101100", "name": "Central Station", "lat": -33.884024, "lon": 151.206203, "mode": "Train / Metro / Light Rail"},
    {"id": "10101101", "name": "Town Hall Station", "lat": -33.873212, "lon": 151.206354, "mode": "Train / Light Rail"},
    {"id": "10101102", "name": "Wynyard Station", "lat": -33.865910, "lon": 151.205755, "mode": "Train / Light Rail"},
    {"id": "10101103", "name": "Circular Quay Wharf & Station", "lat": -33.861440, "lon": 151.210740, "mode": "Ferry / Train / Light Rail"},
    {"id": "10101104", "name": "Parramatta Station & Bus Interchange", "lat": -33.817028, "lon": 151.002884, "mode": "Train / Bus"},
    {"id": "10101105", "name": "Chatswood Interchange", "lat": -33.797200, "lon": 151.181200, "mode": "Train / Metro / Bus"},
    {"id": "10101106", "name": "Bondi Junction Interchange", "lat": -33.891500, "lon": 151.247800, "mode": "Train / Bus"},
    {"id": "10101107", "name": "North Sydney Station", "lat": -33.839800, "lon": 151.206600, "mode": "Train / Metro"},
    {"id": "10101108", "name": "Strathfield Station", "lat": -33.871100, "lon": 151.090600, "mode": "Train / Bus"},
    {"id": "10101109", "name": "Macquarie University Station", "lat": -33.777000, "lon": 151.114100, "mode": "Metro / Bus"},
    {"id": "10101110", "name": "Sydney Airport T1 International", "lat": -33.938800, "lon": 151.164400, "mode": "Train"},
    {"id": "10101111", "name": "Sydney Airport T2/T3 Domestic", "lat": -33.933300, "lon": 151.180400, "mode": "Train"},
    {"id": "10101112", "name": "Barangaroo Ferry Wharf", "lat": -33.864000, "lon": 151.201200, "mode": "Ferry"},
    {"id": "10101113", "name": "Redfern Station", "lat": -33.892400, "lon": 151.199600, "mode": "Train"},
    {"id": "10101114", "name": "Blacktown Interchange", "lat": -33.769000, "lon": 150.907300, "mode": "Train / Bus"}
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

        CREATE INDEX IF NOT EXISTS idx_vehicle_timestamp ON vehicle_occupancy (timestamp);
        CREATE INDEX IF NOT EXISTS idx_vehicle_mode ON vehicle_occupancy (mode);
        CREATE INDEX IF NOT EXISTS idx_station_timestamp ON station_foot_traffic (timestamp);
        CREATE INDEX IF NOT EXISTS idx_station_id ON station_foot_traffic (station_id);
    """)

    conn.commit()
    conn.close()


def seed_baseline_history_if_empty(db_path=DB_FILE):
    """Populates historical 24-hour Sydney commute patterns if DB is new/empty."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM snapshots")
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        return

    print("Database is empty. Generating realistic historical Sydney commute baseline...")
    now = datetime.now()
    modes = ["Sydney Trains", "Sydney Metro", "Sydney Buses", "Sydney Ferries", "Light Rail"]

    # Generate 24 hours of hourly snapshots
    for hours_ago in range(24, -1, -1):
        snapshot_time = (now - timedelta(hours=hours_ago)).strftime("%Y-%m-%d %H:00:00")
        hour_of_day = (now - timedelta(hours=hours_ago)).hour

        # Morning Peak (7-9 AM) & Evening Peak (4-7 PM) volume multipliers
        if 7 <= hour_of_day <= 9 or 16 <= hour_of_day <= 18:
            peak_factor = 2.2
        elif 10 <= hour_of_day <= 15:
            peak_factor = 1.1
        elif 20 <= hour_of_day <= 23:
            peak_factor = 0.7
        else:
            peak_factor = 0.3

        cursor.execute(
            "INSERT INTO snapshots (timestamp, run_type, status) VALUES (?, 'SEED_BASELINE', 'SUCCESS')",
            (snapshot_time,)
        )
        snapshot_id = cursor.lastrowid

        # Insert Vehicle Occupancy records
        num_vehicles = int(random.randint(40, 70) * peak_factor)
        for v in range(num_vehicles):
            mode = random.choice(modes)
            
            # Choose occupancy status weighted by hour
            if peak_factor > 1.8:
                occ_status = random.choice(["STANDING_ROOM_ONLY", "CRUSHED_STANDING_ROOM_ONLY", "FEW_SEATS_AVAILABLE", "FULL"])
            elif peak_factor < 0.5:
                occ_status = random.choice(["EMPTY", "MANY_SEATS_AVAILABLE"])
            else:
                occ_status = random.choice(["MANY_SEATS_AVAILABLE", "FEW_SEATS_AVAILABLE", "STANDING_ROOM_ONLY"])
            
            occ_score = OCCUPANCY_MAP.get(occ_status, 50) + random.randint(-5, 5)
            occ_score = max(0, min(100, occ_score))

            # Random Sydney coordinates near CBD or suburban corridors
            lat = -33.87 + random.uniform(-0.15, 0.15)
            lon = 151.20 + random.uniform(-0.30, 0.20)
            speed = round(random.uniform(0, 75), 1)

            cursor.execute("""
                INSERT INTO vehicle_occupancy 
                (snapshot_id, timestamp, vehicle_id, mode, route_id, latitude, longitude, speed, occupancy_status, occupancy_score, trip_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id, snapshot_time, f"{mode[:3].upper()}-{random.randint(1000, 9999)}",
                mode, f"LINE-{random.randint(1, 12)}", lat, lon, speed, occ_status, occ_score, f"TRIP-{random.randint(10000, 99999)}"
            ))

        # Insert Station Foot Traffic records
        for hub in SYDNEY_HUBS:
            base_deps = random.randint(15, 45)
            sched_deps = int(base_deps * peak_factor)
            delayed_deps = int(sched_deps * random.uniform(0.05, 0.25)) if peak_factor > 1.0 else random.randint(0, 2)
            avg_delay = round(random.uniform(30, 240) * (1 if delayed_deps > 0 else 0.2), 1)
            
            # Foot traffic index formula: function of departures, peak factor & random variance
            traffic_idx = min(100.0, round((sched_deps * 1.5 + delayed_deps * 2.0 + (peak_factor * 20)) * random.uniform(0.85, 1.15), 1))
            
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
                (snapshot_id, timestamp, station_id, station_name, latitude, longitude, mode, scheduled_departures, delayed_departures, avg_delay_sec, foot_traffic_index, status_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id, snapshot_time, hub["id"], hub["name"], hub["lat"], hub["lon"],
                hub["mode"], sched_deps, delayed_deps, avg_delay, traffic_idx, status_lvl
            ))

        # Update snapshot summary numbers
        cursor.execute(
            "UPDATE snapshots SET total_vehicles = ?, total_stations = ? WHERE id = ?",
            (num_vehicles, len(SYDNEY_HUBS), snapshot_id)
        )

    conn.commit()
    conn.close()
    print("Baseline history seeded successfully.")


if __name__ == "__main__":
    init_db()
    seed_baseline_history_if_empty()
    print("Database initialized.")

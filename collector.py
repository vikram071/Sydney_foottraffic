import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime
from google.transit import gtfs_realtime_pb2

from db import init_db, get_db_connection, SYDNEY_HUBS, OCCUPANCY_MAP

DEFAULT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJCb3dUU0Z5dEFIWnVpYlZyaGg0RUdlMmtXRzZKLVZMai1HYUFBOENKb2hNIiwiaWF0IjoxNzg2MjU0MDU5fQ.2G96XQVBv-OXBlsiJqKW7IumCdXtCTokaMo7uvIPK_U"

GTFS_ENDPOINTS = {
    "Sydney Trains": "https://api.transport.nsw.gov.au/v2/gtfs/vehiclepos/sydneytrains",
    "Sydney Metro": "https://api.transport.nsw.gov.au/v2/gtfs/vehiclepos/metro",
    "Sydney Buses": "https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/buses",
    "Sydney Ferries": "https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/ferries",
    "Light Rail": "https://api.transport.nsw.gov.au/v1/gtfs/vehiclepos/lightrail"
}

DEPARTURE_MON_BASE = "https://api.transport.nsw.gov.au/v1/tp/departure_mon"


def get_api_key():
    """Returns TfNSW API key from environment variable or fallback."""
    return os.environ.get("TFNSW_API_KEY", DEFAULT_API_KEY)


def fetch_gtfs_realtime_vehicles(api_key):
    """Fetches and parses real-time vehicle positions and occupancy from TfNSW GTFS-R feeds."""
    headers = {"Authorization": f"apikey {api_key}"}
    vehicle_records = []

    # Map GTFS-R occupancy enum to strings
    occ_enum_names = {
        0: "EMPTY",
        1: "MANY_SEATS_AVAILABLE",
        2: "FEW_SEATS_AVAILABLE",
        3: "STANDING_ROOM_ONLY",
        4: "CRUSHED_STANDING_ROOM_ONLY",
        5: "FULL",
        6: "NOT_ACCEPTING_PASSENGERS"
    }

    for mode, url in GTFS_ENDPOINTS.items():
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                content = response.read()
                feed = gtfs_realtime_pb2.FeedMessage()
                feed.ParseFromString(content)

                count = 0
                for entity in feed.entity:
                    if entity.HasField("vehicle"):
                        v = entity.vehicle
                        v_id = v.vehicle.id or v.vehicle.label or entity.id
                        lat = v.position.latitude if v.HasField("position") else None
                        lon = v.position.longitude if v.HasField("position") else None
                        speed = v.position.speed * 3.6 if v.HasField("position") and v.position.speed else 0.0 # m/s to km/h

                        occ_enum = v.occupancy_status if v.HasField("occupancy_status") else None
                        occ_status = occ_enum_names.get(occ_enum, "UNKNOWN")
                        occ_score = OCCUPANCY_MAP.get(occ_status, 40)

                        route_id = v.trip.route_id if v.HasField("trip") else ""
                        trip_id = v.trip.trip_id if v.HasField("trip") else ""

                        if lat and lon and lat != 0 and lon != 0:
                            vehicle_records.append({
                                "vehicle_id": v_id,
                                "mode": mode,
                                "route_id": route_id,
                                "latitude": lat,
                                "longitude": lon,
                                "speed": round(speed, 1),
                                "occupancy_status": occ_status,
                                "occupancy_score": occ_score,
                                "trip_id": trip_id
                            })
                            count += 1

                print(f"  [+] {mode}: Retrieved {count} active vehicle positions & occupancy status")
        except Exception as e:
            print(f"  [-] {mode} fetch warning: {e}")

    return vehicle_records


def fetch_station_departure_monitors(api_key):
    """Fetches departure monitor data for key Sydney interchanges to calculate foot traffic density."""
    headers = {"Authorization": f"apikey {api_key}", "Accept": "application/json"}
    station_records = []

    for hub in SYDNEY_HUBS:
        params = {
            "outputFormat": "rapidJSON",
            "type_dm": "stop",
            "name_dm": hub["id"],
            "coordOutputFormat": "EPSG:4326",
            "mode": "any"
        }
        url = f"{DEPARTURE_MON_BASE}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

                stop_events = data.get("stopEvents", [])
                sched_count = len(stop_events)
                delayed_count = 0
                total_delay_sec = 0

                for event in stop_events:
                    dep_sched = event.get("departureTimePlanned")
                    dep_real = event.get("departureTimeEstimated")

                    if dep_sched and dep_real and dep_real != dep_sched:
                        try:
                            # Estimate delay difference
                            dt_sched = datetime.fromisoformat(dep_sched.replace("Z", "+00:00"))
                            dt_real = datetime.fromisoformat(dep_real.replace("Z", "+00:00"))
                            diff = (dt_real - dt_sched).total_seconds()
                            if diff > 60:
                                delayed_count += 1
                                total_delay_sec += diff
                        except Exception:
                            pass

                avg_delay = round(total_delay_sec / delayed_count, 1) if delayed_count > 0 else 0.0

                # Calculate Foot Traffic Index (0-100 scale)
                hour = datetime.now().hour
                is_peak = (7 <= hour <= 9 or 16 <= hour <= 18)
                peak_bonus = 25 if is_peak else 0

                foot_traffic_index = min(100.0, round((sched_count * 2.2) + (delayed_count * 3.0) + peak_bonus, 1))

                if foot_traffic_index > 75:
                    status_lvl = "HEAVY_CONGESTION"
                elif foot_traffic_index > 50:
                    status_lvl = "BUSY"
                elif foot_traffic_index > 25:
                    status_lvl = "MODERATE"
                else:
                    status_lvl = "LOW"

                station_records.append({
                    "station_id": hub["id"],
                    "station_name": hub["name"],
                    "latitude": hub["lat"],
                    "longitude": hub["lon"],
                    "mode": hub["mode"],
                    "scheduled_departures": sched_count,
                    "delayed_departures": delayed_count,
                    "avg_delay_sec": avg_delay,
                    "foot_traffic_index": foot_traffic_index,
                    "status_level": status_lvl
                })
        except Exception as e:
            print(f"  [-] Station {hub['name']} fetch warning: {e}")

    return station_records


def run_polling_job(db_path="sydney_commute.db"):
    """Executes a full live data polling cycle and saves to SQLite database."""
    print("==================================================")
    print(" Starting TfNSW Sydney Live Data Polling Cycle")
    print(f" Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("==================================================")

    init_db(db_path)
    api_key = get_api_key()

    # 1. Fetch GTFS Realtime Vehicles
    print("\nFetching real-time GTFS vehicle positions & occupancy...")
    vehicles = fetch_gtfs_realtime_vehicles(api_key)

    # 2. Fetch Departure Monitors for Sydney Interchanges
    print("\nFetching Departure Monitor foot traffic for Sydney interchanges...")
    stations = fetch_station_departure_monitors(api_key)

    # 3. Store snapshot in SQLite Database
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO snapshots (timestamp, run_type, total_vehicles, total_stations, status) VALUES (?, 'LIVE_POLL', ?, ?, 'SUCCESS')",
        (now_str, len(vehicles), len(stations))
    )
    snapshot_id = cursor.lastrowid

    # Insert Vehicle records
    for v in vehicles:
        cursor.execute("""
            INSERT INTO vehicle_occupancy
            (snapshot_id, timestamp, vehicle_id, mode, route_id, latitude, longitude, speed, occupancy_status, occupancy_score, trip_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id, now_str, v["vehicle_id"], v["mode"], v["route_id"],
            v["latitude"], v["longitude"], v["speed"], v["occupancy_status"],
            v["occupancy_score"], v["trip_id"]
        ))

    # Insert Station records
    for s in stations:
        cursor.execute("""
            INSERT INTO station_foot_traffic
            (snapshot_id, timestamp, station_id, station_name, latitude, longitude, mode, scheduled_departures, delayed_departures, avg_delay_sec, foot_traffic_index, status_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id, now_str, s["station_id"], s["station_name"], s["latitude"], s["longitude"],
            s["mode"], s["scheduled_departures"], s["delayed_departures"], s["avg_delay_sec"],
            s["foot_traffic_index"], s["status_level"]
        ))

    conn.commit()
    conn.close()

    print("\n==================================================")
    print(f" SUCCESS: Polling snapshot #{snapshot_id} stored.")
    print(f" Saved {len(vehicles)} vehicle records & {len(stations)} station records to {db_path}.")
    print("==================================================")
    return snapshot_id


if __name__ == "__main__":
    run_polling_job()

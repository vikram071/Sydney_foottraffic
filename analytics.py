import sqlite3
import pandas as pd
from db import get_db_connection, DB_FILE


def get_latest_metrics(db_path=DB_FILE):
    """Retrieves top-level summary metrics for dashboard KPI cards."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Get latest snapshot ID
    cursor.execute("SELECT id, timestamp FROM snapshots ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {}

    snapshot_id = row["id"]
    last_timestamp = row["timestamp"]

    # Active vehicle count & avg occupancy
    cursor.execute("""
        SELECT COUNT(*) as vehicle_count, AVG(occupancy_score) as avg_occupancy
        FROM vehicle_occupancy WHERE snapshot_id = ?
    """, (snapshot_id,))
    v_res = cursor.fetchone()

    # Busiest station & avg foot traffic
    cursor.execute("""
        SELECT station_name, MAX(foot_traffic_index) as max_idx, AVG(foot_traffic_index) as avg_idx, SUM(scheduled_departures) as total_deps
        FROM station_foot_traffic WHERE snapshot_id = ?
    """, (snapshot_id,))
    s_res = cursor.fetchone()

    # Get mode counts
    cursor.execute("""
        SELECT mode, COUNT(*) as cnt FROM vehicle_occupancy WHERE snapshot_id = ? GROUP BY mode
    """, (snapshot_id,))
    mode_counts = {r["mode"]: r["cnt"] for r in cursor.fetchall()}

    conn.close()

    return {
        "snapshot_id": snapshot_id,
        "timestamp": last_timestamp,
        "active_vehicles": v_res["vehicle_count"] or 0,
        "avg_occupancy_pct": round(v_res["avg_occupancy"] or 0.0, 1),
        "busiest_station": s_res["station_name"] or "N/A",
        "busiest_station_index": round(s_res["max_idx"] or 0.0, 1),
        "avg_station_foot_traffic": round(s_res["avg_idx"] or 0.0, 1),
        "total_departures": s_res["total_deps"] or 0,
        "mode_counts": mode_counts
    }


def get_vehicle_occupancy_df(db_path=DB_FILE, limit_latest=True):
    """Returns pandas DataFrame of vehicle positions and occupancy."""
    conn = get_db_connection(db_path)
    if limit_latest:
        query = """
            SELECT v.* FROM vehicle_occupancy v
            INNER JOIN (SELECT id FROM snapshots ORDER BY id DESC LIMIT 1) s
            ON v.snapshot_id = s.id
        """
    else:
        query = "SELECT * FROM vehicle_occupancy"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_station_foot_traffic_df(db_path=DB_FILE, limit_latest=True):
    """Returns pandas DataFrame of station foot traffic and delays."""
    conn = get_db_connection(db_path)
    if limit_latest:
        query = """
            SELECT st.* FROM station_foot_traffic st
            INNER JOIN (SELECT id FROM snapshots ORDER BY id DESC LIMIT 1) s
            ON st.snapshot_id = s.id
            ORDER BY st.foot_traffic_index DESC
        """
    else:
        query = "SELECT * FROM station_foot_traffic ORDER BY foot_traffic_index DESC"

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_hourly_commute_trends_df(db_path=DB_FILE):
    """Returns pandas DataFrame of 24-hour aggregated foot traffic, delays, and vehicle counts."""
    conn = get_db_connection(db_path)
    query = """
        SELECT 
            strftime('%Y-%m-%d %H:00:00', s.timestamp) as hour_bucket,
            COUNT(DISTINCT v.id) as vehicle_count,
            ROUND(AVG(v.occupancy_score), 1) as avg_vehicle_occupancy,
            ROUND(AVG(st.foot_traffic_index), 1) as avg_foot_traffic,
            SUM(st.scheduled_departures) as total_scheduled_deps,
            SUM(st.delayed_departures) as total_delayed_deps,
            ROUND(AVG(st.avg_delay_sec), 1) as avg_delay_seconds
        FROM snapshots s
        LEFT JOIN vehicle_occupancy v ON v.snapshot_id = s.id
        LEFT JOIN station_foot_traffic st ON st.snapshot_id = s.id
        GROUP BY hour_bucket
        ORDER BY hour_bucket ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_mode_breakdown_df(db_path=DB_FILE):
    """Returns pandas DataFrame summarizing vehicle count and occupancy by mode."""
    conn = get_db_connection(db_path)
    query = """
        SELECT 
            mode,
            COUNT(*) as vehicle_count,
            ROUND(AVG(occupancy_score), 1) as avg_occupancy,
            SUM(CASE WHEN occupancy_status IN ('STANDING_ROOM_ONLY', 'CRUSHED_STANDING_ROOM_ONLY', 'FULL') THEN 1 ELSE 0 END) as high_occupancy_count
        FROM vehicle_occupancy
        WHERE snapshot_id = (SELECT id FROM snapshots ORDER BY id DESC LIMIT 1)
        GROUP BY mode
        ORDER BY vehicle_count DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


if __name__ == "__main__":
    metrics = get_latest_metrics()
    print("Latest Metrics Summary:", metrics)
    df_v = get_vehicle_occupancy_df()
    print(f"Vehicle DF shape: {df_v.shape}")
    df_s = get_station_foot_traffic_df()
    print(f"Station DF shape: {df_s.shape}")

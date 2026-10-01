import math
import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def recommend_response(item: dict) -> dict:
    """Recommend priority, crew type, action, and timeframe based on incident/hotspot attributes."""
    waste = item.get("waste_type", item.get("dominant_waste_type", "household garbage"))
    severity = item.get("severity", item.get("avg_severity", 3))
    count = item.get("incident_count", 1)

    if waste in ["medical waste", "industrial waste"] or severity >= 4.5:
        return {
            "priority": "P1 - Critical",
            "crew_type": "Hazmat & Specialized Clean-up Unit",
            "action": "Immediate containment, safe disposal, and environmental hazard inspection.",
            "suggested_timeframe": "Within 6 hours",
            "priority_score": 100,
        }
    elif waste == "construction debris" or count >= 8:
        return {
            "priority": "P2 - High",
            "crew_type": "Heavy Machinery & Dump Truck Crew",
            "action": "Clear debris using excavators, issue enforcement/fine notices to local contractors.",
            "suggested_timeframe": "Within 24 hours",
            "priority_score": 75,
        }
    elif waste == "e-waste":
        return {
            "priority": "P2 - High",
            "crew_type": "E-waste Recycling Taskforce",
            "action": "Collect electronics safely for authorized e-recycling facilities.",
            "suggested_timeframe": "Within 24-48 hours",
            "priority_score": 70,
        }
    else:
        return {
            "priority": "P3 - Moderate",
            "crew_type": "Standard Municipal Sanitation Crew",
            "action": "Routine waste collection; deploy CCTV or warning signs if recurrent.",
            "suggested_timeframe": "Within 48 hours",
            "priority_score": 45,
        }


def solve_nearest_neighbor_route(points: list, depot: list = None):
    """Simple nearest-neighbor TSP route optimizer starting from depot."""
    if not points:
        return []

    start = depot or config.DEFAULT_MAP_CENTER
    unvisited = points.copy()
    current = start
    route = []

    while unvisited:
        nearest_idx = 0
        min_dist = float("inf")
        for idx, pt in enumerate(unvisited):
            d = math.hypot(pt["lat"] - current[0], pt["lon"] - current[1])
            if d < min_dist:
                min_dist = d
                nearest_idx = idx

        next_pt = unvisited.pop(nearest_idx)
        route.append(next_pt)
        current = [next_pt["lat"], next_pt["lon"]]

    return route


def rank_priorities(hotspots_summary: pd.DataFrame) -> list:
    """Rank hotspots by priority score and generate optimized cleanup route sequence."""
    if hotspots_summary.empty:
        return []

    ranked = []
    for _, row in hotspots_summary.iterrows():
        rec = recommend_response(row.to_dict())
        ranked.append({
            "cluster_id": int(row["cluster_id"]),
            "locality": row["nearest_locality"],
            "lat": row["center_lat"],
            "lon": row["center_lon"],
            "incident_count": int(row["incident_count"]),
            "dominant_waste": row["dominant_waste_type"],
            "priority": rec["priority"],
            "priority_score": rec["priority_score"],
            "crew_type": rec["crew_type"],
            "action": rec["action"],
            "timeframe": rec["suggested_timeframe"],
        })

    # Sort by priority score descending
    ranked.sort(key=lambda x: (x["priority_score"], x["incident_count"]), reverse=True)

    # Calculate optimal TSP route order
    route_ordered = solve_nearest_neighbor_route(ranked, depot=config.DEFAULT_MAP_CENTER)
    for step, item in enumerate(route_ordered, start=1):
        item["route_order"] = step

    return route_ordered

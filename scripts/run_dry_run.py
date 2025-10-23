#!/usr/bin/env python3
"""
Run a dry-run of Greedy algorithm with synthetic data and generate reports.
"""
import random
from datetime import time
import os

from app.algorithms.greedy import Greedy


def build_test_data():
    instructors = []
    for i in range(1, 22):
        instructors.append({"id": i, "name": f"Instructor {i}", "type": "instructor" if i <= 18 else "assistant"})

    projects = []
    # 50 ara projects
    for i in range(1, 51):
        projects.append({"id": 1000 + i, "title": f"Ara Project {i}", "type": "ara", "responsible_id": random.choice(instructors)["id"]})
    # 31 bitirme projects
    for i in range(1, 32):
        projects.append({"id": 2000 + i, "title": f"Bitirme Project {i}", "type": "bitirme", "responsible_id": random.choice(instructors)["id"]})

    classrooms = []
    for i, name in enumerate(["C1", "C2", "C3", "C4", "C5", "C6"], start=1):
        classrooms.append({"id": i, "name": name, "capacity": 40})

    # timeslots 09:00-09:30 ... 16:00-16:30 (half-hour slots)
    times = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00"]
    timeslots = []
    tid = 1
    for t in times:
        timeslots.append({"id": tid, "start_time": t + ":00", "time_range": f"{t}-{t}", "is_morning": t.startswith("09") or t.startswith("10") or t.startswith("11")})
        tid += 1

    data = {"instructors": instructors, "projects": projects, "classrooms": classrooms, "timeslots": timeslots}
    return data


def main():
    random.seed(0)
    data = build_test_data()

    algo = Greedy(params={"time_limit": 2})
    print("Running Greedy dry-run...")
    result = algo.execute(data)

    print("Result keys:", list(result.keys()))
    # List reports directory
    repdir = os.path.join("reports")
    if os.path.isdir(repdir):
        print("Reports written:")
        for f in os.listdir(repdir):
            print(" -", os.path.join(repdir, f))
    else:
        print("No reports directory found.")

    # Print brief summary
    dr = result.get("duplicate_report")
    if dr:
        print("Duplicates summary:", dr.get("summary"))

    cr = result.get("coverage_report")
    if cr:
        print("Coverage:", cr.get("expected_count"), "expected vs scheduled", cr.get("scheduled_count"))

    gr = result.get("gap_report")
    if gr:
        print("Gaps total:", gr.get("total_gaps"))

    print("Dry-run complete.")


if __name__ == '__main__':
    main()






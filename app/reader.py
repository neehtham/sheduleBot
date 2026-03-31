import json
from datetime import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta
from pathlib import Path

# Set base directory for data files (project root / data)
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
SCHEDULE_DIR = DATA_DIR / "schedules"


def finder(intakeCode, groupCode, acc):
    # lecture_file = DATA_DIR / "lectureShedule.json"
    lecture_file = SCHEDULE_DIR / f"{intakeCode}.json"
    bus_file = DATA_DIR / "busShedule.json"

    try:
        if not lecture_file.exists():
            return "Lecture schedule not available yet."
        with open(lecture_file, "r", encoding="utf-8") as l_file:
            lectures = json.load(l_file)

        if not bus_file.exists():
            return "Bus schedule not available yet."
        with open(bus_file, "r", encoding="utf-8") as b_file:
            buses = json.load(b_file)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return f"Error reading schedules: {e}"

    day_lectures = []
    today = datetime.now().date()
    # today = parser.parse("2026-03-26", dayfirst=True).date()

    for lecture in lectures:
        try:
            class_date = parser.parse(lecture["date"], dayfirst=True).date()
            if (
                # intakeCode == lecture["intake"]
                groupCode == lecture["group"] and today == class_date
            ):
                day_lectures.append(lecture)
        except Exception:
            continue

    online_l = []
    physical_l = []
    for l in day_lectures:
        # Check for online rooms (using the existing logic pattern)
        if "ONLMCO3" in l["room"].upper() or "ONLINE" in l["room"].upper():
            online_l.append(l)
        else:
            physical_l.append(l)

    # Prioritize physical classes for bus calculation
    location = acc
    going_bus = []
    returning_bus = []

    if physical_l:
        # Sort by start time to get first and last classes correctly
        physical_l.sort(key=lambda x: parser.parse(x["start"]).time())

        first_l_start = parser.parse(physical_l[0]["start"])
        last_l_end = parser.parse(physical_l[-1]["end"])

        # Buffer: Arrive at least 20 mins before class, leave at least 10 mins after class
        arrival_deadline = (first_l_start - relativedelta(minutes=20)).time()
        departure_earliest = (last_l_end + relativedelta(minutes=10)).time()

        # Latest bus arriving before the deadline
        going_buses = [
            bus
            for bus in buses
            if bus["from"].lower() == location.lower()
            and parser.parse(bus["time"]).time() <= arrival_deadline
        ]
        if going_buses:
            going_bus = [max(going_buses, key=lambda b: parser.parse(b["time"]).time())]

        # Earliest bus returning after the last lecture
        returning_buses = [
            bus
            for bus in buses
            if bus["to"].lower() == location.lower()
            and parser.parse(bus["time"]).time() >= departure_earliest
        ]
        if returning_buses:
            returning_bus = [
                min(returning_buses, key=lambda b: parser.parse(b["time"]).time())
            ]

    output = ""
    if physical_l:
        if going_bus and returning_bus:
            output += f"🗓 You have {len(physical_l)} physical classes today.\n"
            output += f"🚌 Going bus: {going_bus[0]['time']}\n"
            output += f"🚌 Returning bus: {returning_bus[0]['time']}\n\n"
        else:
            output += f"🗓 You have {len(physical_l)} physical classes today.\n"
            if not going_bus:
                output += "⚠️ No suitable going bus found.\n"
            if not returning_bus:
                output += "⚠️ No suitable returning bus found.\n"
            output += "\n"

        for l in physical_l:
            output += (
                f"🔹 {l['name']}\n   ⌚️ {l['start']} - {l['end']}\n   📍 {l['room']}\n"
            )
    else:
        output += "✨ No physical classes today.\n"

    if online_l:
        output += f"\n💻 You have {len(online_l)} online classes:\n"
        for l in online_l:
            output += f"🔹 {l['name']}\n   ⌚️ {l['start']} - {l['end']}\n"
    else:
        output += "✨ No online classes today.\n"

    return output


if __name__ == "__main__":
    # Test call
    print(finder("APU2F2602SE", "G1", "City Of Green"))
    pass

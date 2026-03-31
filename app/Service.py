import requests
import json
from dateutil import parser
import asyncio
from pathlib import Path

# Set base directory for data files (project root / data)
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
SCHEDULE_DIR = DATA_DIR / "schedules"


def get_degree_dir(intake: str):
    degree = intake[:4]
    degree_dir = SCHEDULE_DIR / f"{degree}"
    if not degree_dir.exists():
        degree_dir.mkdir()
    return degree_dir


def get_intake_dir(intake: str):
    intake_dir = get_degree_dir(intake) / f"{intake[:7]}"
    if not intake_dir.exists():
        intake_dir.mkdir()
    return intake_dir


def create_intake_schedule(intake: str, intake_schedules: list):
    intake_dir = get_intake_dir(intake)
    intake_schedule = intake_dir / f"{intake}.json"
    with open(intake_schedule, "w", encoding="utf-8") as f:
        json.dump(intake_schedules, f, indent=4)


def getting_sync():
    if not SCHEDULE_DIR.exists():
        SCHEDULE_DIR.mkdir()
    url = "https://s3-ap-southeast-1.amazonaws.com/open-ws/weektimetable"
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "Referer": "https://apspace.apu.edu.my/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        # cleaned = []
        cleaned = {}
        for entry in data:
            strip_str = entry["INTAKE"].strip()
            if cleaned.get(strip_str) is None:
                cleaned[strip_str] = []
            date_obj = parser.parse(entry["DATESTAMP"])
            simplified = {
                # "intake": entry["INTAKE"],
                "name": entry["MODULE_NAME"],
                "room": entry["ROOM"],
                "date": date_obj.strftime("%d, %m, %Y"),
                "start": entry["TIME_FROM"],
                "end": entry["TIME_TO"],
                "group": entry["GROUPING"],
            }
            cleaned[strip_str].append(simplified)
            # create_intake_schedule(entry["INTAKE"], simplified)
            # cleaned.append(simplified)
        for intake, schedule in cleaned.items():
            create_intake_schedule(intake, schedule)

        # output_file = DATA_DIR / "lectureShedule.json"
        # with open(output_file, "w", encoding="utf-8") as file:
        #     json.dump(cleaned, file, indent=4)
        #
        # print(f"JSON data saved successfully to {output_file}!")
        print("JSON data saved successfully!")
        return True
    except Exception as e:
        print(f"Failed to fetch or save data: {e}")
        return False


async def getting():
    """Async wrapper for the synchronous getting_sync function."""
    return await asyncio.to_thread(getting_sync)


if __name__ == "__main__":
    asyncio.run(getting())

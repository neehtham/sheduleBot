import requests
import json
from dateutil import parser
def getting():

  url = "https://s3-ap-southeast-1.amazonaws.com/open-ws/weektimetable"

  payload = {}
  headers = {
    'sec-ch-ua-platform': '"Windows"',
    'Referer': 'https://apspace.apu.edu.my/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    'x-refresh': '',
    'Accept': 'application/json, text/plain, */*',
    'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    'sec-ch-ua-mobile': '?0'
  }

  response = requests.request("GET", url, headers=headers, data=payload)
  cleaned = []
  if response.status_code == 200:
    data = response.json()  # Convert response to JSON
    for entry in data:
      date_obj = parser.parse(entry["DATESTAMP"])
      intake = entry["INTAKE"]
      name = entry["MODULE_NAME"]
      room = entry["ROOM"]
      date = date_obj.strftime("%d, %m, %Y")
      start = entry["TIME_FROM"]
      end = entry["TIME_TO"]
      group = entry["GROUPING"]
      simplified = {
        "intake": intake,
        "name": name,
        "room": room,
        "date": date,
        "start": start,
        "end": end,
        "group": group
      }
      cleaned.append(simplified)
    # Save to a JSON file
    with open("lectureShedule.json", "w", encoding="utf-8") as file:
        json.dump(cleaned, file, indent=4)  # Pretty print with indent

    print("JSON data saved successfully!")
  else:
    print(f"Failed to fetch data. Status code: {response.status_code}")

  
getting()
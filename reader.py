import json
from datetime import *
from dateutil import parser
from dateutil.relativedelta import *
def finder(intakeCode, groupCode, acc):
    with open('lectureShedule.json','r')as L:
        file_contects = L.read()
    lectures = json.loads(file_contects)
    
    with open('busShedule.json','r')as B:
        file_contects = B.read()
    buses = json.loads(file_contects)
    
    dayLectures = []

    for lecture in lectures:
        today = str(datetime.today())
        # today = "08-05-2025"
        today = parser.parse(today)
        classDate = parser.parse(lecture['date'],dayfirst=True)
        if intakeCode == lecture['intake'] and groupCode == lecture['group'] and (today.date()) == (classDate.date()):
            dayLectures.append(lecture)
            continue
        else:
            continue

    online_l = []
    physical_l = []
    for l in dayLectures:
        if 'ONLMCO3' in l['room']:
            online_l.append(l)
        else:
            physical_l.append(l)
    dayLectures = physical_l
    location = acc
    goingBus = []
    returingBus = []
    
    if dayLectures:
        first_l = (parser.parse(dayLectures[0]["start"]) + relativedelta(minutes=-30)).time()
        last_l =  (parser.parse(dayLectures[-1]["end"]) + relativedelta(minutes=+10)).time()
        goingBus = [
            bus for bus in buses
            if bus["from"] == location and parser.parse(bus["time"]).time() < first_l
        ]
        if goingBus:
            goingBus = [max(goingBus, key=lambda b: parser.parse(b["time"]).time())]
        else:
            goingBus = []

        # Find the earliest bus returning from the location after the last lecture
        returingBus = [
            bus for bus in buses
            if bus["to"] == location and parser.parse(bus["time"]).time() > last_l
        ]
        if returingBus:
            returingBus = [min(returingBus, key=lambda b: parser.parse(b["time"]).time())]
        else:
            returingBus = []

    output = f''
    if dayLectures:
        output += f"You have {len(dayLectures)} physical classes today.\nYour going bus is in {goingBus[0]['time']}.\nYour returning bus is in {returingBus[0]['time']}.\n\n"
        for l in dayLectures:
            output += f"{l['name']} from {l['start']} to {l['end']} in {l['room']}\n"
    else:
        output += "You don't have a physical class today\n"
    if online_l:
        output += f'\nYou have {len(online_l)} online classes\n'
        for l in online_l:
            output += f"{l['name']} from {l['start']} to {l['end']}\n"
    else:
        output += "You don't have a online class today\n"
    return output
print(finder('APD1F2503SE','G1','City of Green'))

import json
from dateutil import parser

def process_bus_schedule(input_file, output_file):
    # Read the JSON file
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Process each schedule entry
    simplified_data = []
    for entry in data["trips"]:
        #Parse the time string
        time_obj = parser.parse(entry["time"])
        formatted_time = time_obj.strftime("%I:%M %p")
        # Format the date
        formatted_date = time_obj.strftime("%d, %m, %Y")
        
        # Format the day range
        day_range = entry["day"].replace("mon-fri", "Monday-Friday").replace("sat", "Saturday").replace("sun", "Sunday")
        
        # Extract the from and to locations
        trip_from = entry["trip_from"]["name"]
        trip_to = entry["trip_to"]["name"]
        
        # Create a simplified entry
        simplified_entry = {
            "time": formatted_time,
            "from": trip_from,
            "to": trip_to,
            "day": day_range,
            "date": formatted_date
        }
        
        simplified_data.append(simplified_entry)
    
    # Write the processed data to the output file
    with open(output_file, 'w') as f:
        json.dump(simplified_data, f, indent=2)
    
    print(f"Successfully processed {len(simplified_data)} bus schedule entries.")
    return simplified_data

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python bus_schedule_parser.py input_file.json output_file.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        process_bus_schedule(input_file, output_file)
        print(f"Data has been processed and saved to {output_file}")
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)
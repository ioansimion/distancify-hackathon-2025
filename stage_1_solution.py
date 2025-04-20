import requests
import math
import numpy as np

BASE_URL = "http://localhost:5000"
TARGET_DISPATCHES = 10
MAX_ACTIVE_CALLS = 3

# Example endpoint
# response = requests.get(f"{BASE_URL}/locations")

# # Check if it worked
# if response.status_code == 200:
#     data = response.json()  # Convert JSON to Python dictionary/list
#     print(data[0]["lat"], data[0]["long"])
# else:
#     print(f"Error: {response.status_code}")


# START
def start_scenario():
    payload = {
        "seed": "default",
        "targetDispatches": TARGET_DISPATCHES,
        "maxActiveCalls": MAX_ACTIVE_CALLS - 1,
    }
    response = requests.post(f"{BASE_URL}/control/reset", params=payload)
    return response.json()


# STOP
def stop_scenario():
    response = requests.post(f"{BASE_URL}/control/stop")
    return response.json()


def scenario_status():
    response = requests.get(f"{BASE_URL}/control/status")
    return response.json()


# NEXT
def get_next_call():
    response = requests.get(f"{BASE_URL}/calls/next")
    return response.json()


# QUEUE
def get_calls_queue():
    response = requests.get(f"{BASE_URL}/calls/queue")
    return response.json()


# FILL
def fill_calls_queue():
    queue = []
    for _ in range(MAX_ACTIVE_CALLS):
        queue.append(get_next_call())

    return queue


# LOCATIONS
def get_locations():
    response = requests.get(f"{BASE_URL}/locations")
    if not response.ok:
        raise Exception(response.text)

    locations = response.json()
    return locations


# MEDICAL LOCATIONS
def get_medical_locations():
    response = requests.get(f"{BASE_URL}/medical/search")
    if not response.ok:
        raise Exception("Failed to fetch /medical/search")

    medical_data = response.json()

    medical_locations = []
    for entry in medical_data:
        if entry["quantity"] > 0:
            medical_locations.append(entry)

    return medical_locations


# MEDICAL BY CITY
def get_medical_by_city(county, city):
    params = {"county": county, "city": city}
    response = requests.get(f"{BASE_URL}/medical/searchbycity", params=params)
    if not response.ok:
        raise Exception("Failed to fetch /medical/searchbycity")

    data = response.json()
    return data


# DISPATCH
def dispatch(sourceCounty, sourceCity, targetCounty, targetCity, quantity):
    payload = {
        "sourceCounty": sourceCounty,
        "sourceCity": sourceCity,
        "targetCounty": targetCounty,
        "targetCity": targetCity,
        "quantity": quantity,
    }
    response = requests.post(f"{BASE_URL}/medical/dispatch", json=payload)
    return response


def get_locations_coords(locations):
    locations_coords = {}
    for location in locations:
        county = location["county"]
        city = location["name"]
        lat = location["lat"]
        long = location["long"]
        locations_coords[(county, city)] = (lat, long)

    return locations_coords


def euclidean(p1, p2):
    return math.sqrt((p1["lat"] - p2["lat"]) ** 2 + (p1["long"] - p2["long"]) ** 2)


if __name__ == "__main__":
    print(start_scenario()["targetDispatches"], start_scenario()["maxActiveCalls"] + 1)

    locations = get_locations()
    num_locations = len(locations)
    locations_coords = get_locations_coords(locations=locations)

    # Create and calculate the distance matrix (dict)
    distance_matrix = {}
    for source in locations:
        source_key = (source["county"], source["name"])
        distance_matrix[source_key] = {}
        for target in locations:
            target_key = (target["county"], target["name"])
            distance = euclidean(source, target)
            distance_matrix[source_key][target_key] = distance

    calls_queue = get_calls_queue()
    print(calls_queue)
    calls_queue = fill_calls_queue()
    print(calls_queue)
    calls_queue = get_calls_queue()
    print(calls_queue)
    num_calls = len(calls_queue)

    medical_locations = get_medical_locations()
    num_medical_locations = len(medical_locations)

    print(distance_matrix["Maramureș", "Baia Mare"]["Maramureș", "Baia Sprie"])

    print(stop_scenario())

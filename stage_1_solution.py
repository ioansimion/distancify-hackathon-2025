import requests
import math

BASE_URL = "http://localhost:5000"
SEED = "default"
TARGET_DISPATCHES = 10
MAX_ACTIVE_CALLS = 3


# region Control
def start_scenario():
    payload = {
        "seed": SEED,
        "targetDispatches": TARGET_DISPATCHES,
        "maxActiveCalls": MAX_ACTIVE_CALLS - 1,
    }
    response = requests.post(f"{BASE_URL}/control/reset", params=payload)
    return response.json()


def stop_scenario():
    response = requests.post(f"{BASE_URL}/control/stop")
    return response.json()


def scenario_status():
    response = requests.get(f"{BASE_URL}/control/status")
    return response.json()


# endregion Control


# region Calls
def get_next_call():
    response = requests.get(f"{BASE_URL}/calls/next")
    if response.ok:
        return response.json()
    else:
        return None


def get_calls_queue():
    response = requests.get(f"{BASE_URL}/calls/queue")
    return response.json()


def fill_calls_queue(queue: list = None):
    """
    Fills the call queue until reaching MAX_ACTIVE_CALLS or emergencies(TARGET_DISPATCHES) are exhausted
    """
    if queue is None:
        queue = []

    active_calls = len(queue)
    current_target = sum(call["requests"][0]["Quantity"] for call in queue)

    while (active_calls < MAX_ACTIVE_CALLS) and (current_target < TARGET_DISPATCHES):
        call = get_next_call()
        if call is None:
            break

        queue.append(call)

        active_calls += 1
        current_target += call["requests"][0]["Quantity"]

    return queue


# endregion Calls


# region Locations
def get_locations():
    response = requests.get(f"{BASE_URL}/locations")
    if not response.ok:
        raise Exception(response.text)

    locations = response.json()
    return locations


# endregion Locations


# region Medical
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


def get_medical_by_city(county, city):
    params = {"county": county, "city": city}
    response = requests.get(f"{BASE_URL}/medical/searchbycity", params=params)
    if not response.ok:
        raise Exception("Failed to fetch /medical/searchbycity")

    data = response.json()
    return data


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


# endregion Medical


# region Utils
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


# endregion Utils


if __name__ == "__main__":
    start_response = start_scenario()

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

    calls_queue = []
    calls_queue = fill_calls_queue(calls_queue)
    print(calls_queue)
    for call in calls_queue:
        dispatch(
            sourceCounty="Maramureș",
            sourceCity="Baia Mare",
            targetCounty=call["county"],
            targetCity=call["city"],
            quantity=call["requests"][0]["Quantity"],
        )
    calls_queue = get_calls_queue()
    print(calls_queue)
    calls_queue = fill_calls_queue(calls_queue)
    calls_queue = fill_calls_queue(calls_queue)
    print(calls_queue)
    num_calls = len(calls_queue)

    medical_locations = get_medical_locations()
    num_medical_locations = len(medical_locations)

    stop_response = stop_scenario()
    print(
        stop_response["runningTime"],
        "  ",
        stop_response["requestCount"],
        "or",
        stop_response["httpRequests"],
        "  ",
        stop_response["penalty"],
        stop_response["errors"]["missed"],
        stop_response["errors"]["overDispatched"],
    )

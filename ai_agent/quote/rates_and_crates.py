import json
from typing import Dict, Any

def load_db():
    try:
        db = {}
        base_path = "data"

        with open(f"{base_path}/customer_profile.json", "r", encoding="utf-8") as f:
            db["customers"] = json.load(f)
        with open(f"{base_path}/distances.json", "r", encoding="utf-8") as f:
            db["distances"] = json.load(f)
        with open(f"{base_path}/rates.json", "r", encoding="utf-8") as f:
            db["rates"] = json.load(f)
        with open(f"{base_path}/crates.json", "r", encoding="utf-8") as f:
            db["crates"] = json.load(f)
        with open(f"{base_path}/breeds.json", "r", encoding="utf-8") as f:
            db["breeds"] = json.load(f)
        with open(f"{base_path}/airlines.json", "r", encoding="utf-8") as f:
            db["airlines"] = json.load(f)
        with open(f"{base_path}/drivers.json", "r", encoding="utf-8") as f:
            db["drivers"] = json.load(f)
        return db
    except Exception as e:
        return {"error": f"Error loading database: {str(e)}"}

db = load_db()

def get_distance(from_location, to_location):
    distances = db.get("distances", {})
    entries = distances.get(from_location, [])
    for record in entries:
        if record["arrival_airport"].lower() in to_location.lower():
            return record["distance"]
    return 100

def get_nearest_origin_airports(origin):
    airlines = db["airlines"]
    airports = ['ATL', 'AUS', 'BNA', 'BOS', 'BWI', 'CLE', 'CLT', 'CVG', 'DEN', 'DFW',
                'DTW', 'EWR', 'IAD', 'IAH', 'JFK', 'LAS', 'LAX', 'MCO', 'MIA', 'MSP',
                'MSY', 'ORD', 'PDX', 'PHL', 'PHX', 'PIT', 'SAN', 'SEA', 'SFO', 'SJC',
                'SLC', 'STL', 'TPA']
    distances = [{'airport': airport, 'distance': get_distance(origin, airport)} for airport in airports]
    options = sorted([d for d in distances if d["distance"] is not None], key=lambda x: x["distance"])[:3]
    for option in options:
        option["airlines"] = [airline["airline"] for airline in airlines if any(
            option["airport"] in entry.get("airports", []) for entry in airline.get("airportsByCountry", []))]
    return options

def get_nearest_destination_airports(dest_city, dest_country):
    airlines = db["airlines"]
    dest_airports = {airport for airline in airlines for entry in airline.get("airportsByCountry", [])
                     if entry.get("country", "").lower() == dest_country.lower()
                     for airport in entry.get("airports", [])}
    distances = [{'airport': airport, 'distance': get_distance(f"{dest_city}, {dest_country}", airport)}
                 for airport in dest_airports]
    options = sorted([d for d in distances if d["distance"] is not None], key=lambda x: x["distance"])[:3]
    for option in options:
        option["airlines"] = list({airline["airline"] for airline in airlines for entry in airline.get("airportsByCountry", [])
                                   if entry.get("country", "").lower() == dest_country.lower() and
                                   option["airport"] in entry.get("airports", [])})
    return options

def map_crate(length, height):
    min_length = (height / 4) + length + 3
    min_height = height + 3
    crates = sorted(db['crates'], key=lambda c: c["ext_dim"]["length"])
    return next((crate for crate in crates if crate["ext_dim"]["length"] >= min_length and
                crate["ext_dim"]["height"] >= min_height), None)

def get_crate_sizes(pets):
    selected_crates, total_chargeable_kilos, crate_fee, total_width = [], 0, False, 0
    for pet in pets:
        crate = map_crate(pet['length_in'], pet['height_in'])
        if not crate: continue
        ext = crate["ext_dim"]
        if ext["height"] > 35: crate_fee = True
        total_chargeable_kilos += (ext["length"] * ext["width"] * ext["height"]) / 6000
        selected_crates.append(crate)
        total_width += ext["width"]
    if total_width > 35: crate_fee = True
    return selected_crates, round(total_chargeable_kilos, 2), crate_fee

def map_rate(charged_kg, airline, rates):
    tiers = ["500+", "300+", "100+", "45+", "<45", "+500", "+300", "+100", "+45", "1000"]
    for tier in tiers:
        if tier in rates and charged_kg >= int(''.join(filter(str.isdigit, tier))):
            return max(rates["Min"], charged_kg * rates[tier])
    return max(rates["Min"], charged_kg * rates.get("PerKg", rates.get("Nominal", 0)))

def get_transportation_fee(distance):
    rate = 1.75 if distance < 250 else 1.5 if distance < 500 else 1.25 if distance < 1000 else 1.0
    total_fee = distance * rate
    while distance > 500:
        total_fee += 150
        distance -= 500
    return total_fee

def get_banned_breeds(dest_country, pets):
    allowed_lists, breeds = [], db['breeds']
    for pet in pets:
        pet_breed = pet["breed"].lower().strip()
        for breed in breeds:
            if breed["breed"].lower() == pet_breed:
                if dest_country.lower() in [x.lower() for x in breed.get("countriesThatBan", [])]:
                    return True, [], "country ban"
                allowed_lists.append(breed.get("airlinesThatAllow", []))
    if not allowed_lists or any(not a for a in allowed_lists):
        return True, [], "all airline ban"
    allowed_airlines = set(allowed_lists[0])
    for lst in allowed_lists[1:]: allowed_airlines.intersection_update(lst)
    return True, list(allowed_airlines), ""

def get_rates_and_crates(origin, dest_city, dest_country, transport, pets):
    banned, allowed_airlines, msg = get_banned_breeds(dest_country, pets)
    if msg == "country ban":
        return f"No routes or rates possible. {dest_country} bans the import of one or more pets."
    if msg == "all airline ban":
        return f"No routes or rates possible. All airlines ban the import of one or more pets."
    origin_options = get_nearest_origin_airports(origin)
    dest_options = get_nearest_destination_airports(dest_city, dest_country)
    selected_crates, total_kgs, crate_fee = get_crate_sizes(pets)
    airline_lookup = {a["_id"]: a["airline"] for a in db["airlines"]}
    routes = []
    for o in origin_options:
        for d in dest_options:
            for rate in db["rates"]:
                if rate["fromAirport"] == o["airport"] and rate["toAirport"] == d["airport"]:
                    airline = airline_lookup.get(rate["airlineId"], "Unknown")
                    if not banned or airline in allowed_airlines:
                        cost = round(map_rate(total_kgs, airline, rate["rates"]), 2)
                        rate_per_kg = round(cost / total_kgs, 2) if total_kgs > 0 else 0
                        transport_fee = get_transportation_fee(o["distance"]) if transport else None
                        routes.append({
                            "originAirport": o["airport"],
                            "originAirportDistance": o["distance"],
                            "ground_transportation_fee": transport_fee,
                            "destAirport": d["airport"],
                            "destAirportDistance": d["distance"],
                            "airline": airline,
                            "ratePerKg": rate_per_kg,
                            "rateTotal": cost
                        })
    return {
        "rates": routes,
        "crates": selected_crates,
        "checkin_fee": 300.0,
        "oversized_crate_fee": 150.0 if crate_fee and transport else None
    }

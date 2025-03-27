from langchain_core.tools import tool
import json

def load_drivers():
    with open("data/drivers.json", "r") as f:
        return json.load(f)

@tool
def ground_transfer_agent_origin(user_info: dict) -> dict:
    """
    Fetches the top 5 drivers available for ground transfer from the origin city.

    The origin and origin_country are extracted from the user's profile (user_info).
    The tool reads from 'drivers.json', filters drivers by city and country,
    sorts them by rating, and returns:
      - 'origin_driver_options': a list of driver details as formatted strings
      - 'origin_driver_emails': the list of email addresses
      - 'ground_transfer_requested': set to True
      - 'current_stage': updated to proceed to destination driver lookup

    If no drivers are found, an error message is returned and ground_transfer_requested is set to False.
    """
    origin = user_info.get("origin")
    origin_country = user_info.get("origin_country", "USA")
    drivers = load_drivers()
    city_drivers = drivers.get(origin_country, {}).get(origin, [])

    if not city_drivers:
        return {
            "error": f"No drivers found in origin: {origin}, {origin_country}",
            "ground_transfer_requested": False,
            "current_stage": "awaiting_ground_transfer_decision"
        }

    sorted_drivers = sorted(city_drivers, key=lambda d: d["driver_rating"], reverse=True)[:5]
    return {
        "ground_transfer_requested": True,
        "origin_driver_options": [
            f"ID: {d['driver_id']}, Name: {d['driver_name']}, Email: {d['driver_email']}, Rating: {d['driver_rating']}"
            for d in sorted_drivers
        ],
        "origin_driver_emails": [d["driver_email"] for d in sorted_drivers],
        "current_stage": "awaiting_ground_transfer_destination"
    }

@tool
def ground_transfer_agent_destination(user_info: dict) -> dict:
    """
    Fetches the top 5 drivers available for ground transfer at the destination city.

    The destination_city and destination_country are extracted from the user's profile (user_info).
    The tool reads from 'drivers.json', filters drivers by city and country,
    sorts them by rating, and returns:
      - 'destination_driver_options': a list of driver details as formatted strings
      - 'destination_driver_emails': the list of email addresses
      - 'current_stage': updated to proceed to flight quote stage

    If no drivers are found, an error message is returned and the flow still proceeds to quote calculation.
    """
    dest_city = user_info.get("destination_city")
    dest_country = user_info.get("destination_country")
    db = load_drivers()
    city_drivers = db.get(dest_country, {}).get(dest_city, [])

    if not city_drivers:
        return {
            "error": f"No drivers found in destination: {dest_city}, {dest_country}",
            "current_stage": "awaiting_quote"
        }

    sorted_drivers = sorted(city_drivers, key=lambda d: d["driver_rating"], reverse=True)[:5]
    return {
        "destination_driver_options": [
            f"ID: {d['driver_id']}, Name: {d['driver_name']}, Email: {d['driver_email']}, Rating: {d['driver_rating']}"
            for d in sorted_drivers
        ],
        "destination_driver_emails": [d["driver_email"] for d in sorted_drivers],
        "current_stage": "awaiting_quote"
    }

@tool
def send_driver_notification(driver_emails: list) -> str:
    """
    Sends dummy email notifications to the given list of driver emails.

    Accepts either:
    - origin_driver_emails
    - destination_driver_emails

    LangGraph's tools_condition or assistant will pass the appropriate field from state.
    """
    if not driver_emails:
        return "No driver emails provided."
    return f"Email notifications sent successfully to: {', '.join(driver_emails)}"
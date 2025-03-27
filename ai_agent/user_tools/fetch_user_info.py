from langchain_core.tools import tool
import json

@tool
def fetch_user_info(user_email: str) -> dict:
    """
    Fetches user information from customers.json using the email.
    Returns user_info and current_stage if found. Includes full error handling.
    """
    with open("data/customer_profile.json", "r", encoding="utf-8") as f:
        customers = json.load(f)

    for customer in customers:
        if customer["email"].strip().lower() == user_email.strip().lower():
            return {
                "user_info": customer,
                "current_stage": "awaiting_ground_transfer"
            }

    return {
        "error": "No user found with that email.",
        "current_stage": "awaiting_email"
    }
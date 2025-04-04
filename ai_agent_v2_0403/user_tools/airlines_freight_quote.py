from langchain_core.tools import tool
from quote.rates_and_crates import get_rates_and_crates

@tool
def airlines_freight_quote(user_info: dict, ground_transfer_requested: bool) -> dict:
    """
    Calculates the total air freight quote including crate size and transport costs.

    Uses user_info to extract:
    - origin
    - destination city & country
    - pets (length, height, weight, breed, etc.)

    Uses ground_transfer_requested to factor in transport costs.
    
    Calculates an accurate pet airline freight quote using airline and crate data.

    This tool should be used when the user:
    - Asks for a price or cost estimate
    - Wants a freight quote or shipping calculation
    - Mentions 'flight quote', 'crate cost', 'airline rate', etc.

    Pulls details from user_info and uses ground_transfer_requested to factor in transport cost.

    Returns total cost, crate size, selected airline, and additional notes.
    """
    try:
        origin = user_info.get("origin")
        dest_city = user_info.get("destination_city")
        dest_country = user_info.get("destination_country")
        pets = user_info.get("pets", [])

        if not all([origin, dest_city, dest_country, pets]):
            return {"error": "Incomplete user information for quote calculation."}

        result = get_rates_and_crates(
            origin=origin,
            dest_city=dest_city,
            dest_country=dest_country,
            transport=ground_transfer_requested,
            pets=pets
        )

        return {
            "flight_quote": result,
            "current_stage": "quote_ready"
        }

    except Exception as e:
        return {
            "error": f"Quote calculation failed: {str(e)}",
            "current_stage": "error"
        }
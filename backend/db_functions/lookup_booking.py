from db import db


async def lookup_booking(
    confirmation_number: str = None,
    guest_name: str = None,
    guest_email: str = None,
    guest_phone: str = None
):
    """Look up a booking by confirmation number, guest name, email, or phone.
    
    Args:
        confirmation_number: The booking confirmation number (e.g., GV-2025-001001)
        guest_name: Guest's full or partial name
        guest_email: Guest's email address
        guest_phone: Guest's phone number
    
    Returns:
        Booking details or error message
    """
    # Build query based on provided parameters
    query = {}
    
    if confirmation_number:
        # Exact match for confirmation number (case-insensitive)
        query["confirmation_number"] = {"$regex": confirmation_number, "$options": "i"}
    elif guest_email:
        # Exact match for email (case-insensitive)
        query["guest_email"] = {"$regex": f"^{guest_email}$", "$options": "i"}
    elif guest_phone:
        # Partial match for phone (in case formatting differs)
        # Remove common phone formatting characters for matching
        clean_phone = guest_phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "").replace("+", "")
        query["guest_phone"] = {"$regex": clean_phone}
    elif guest_name:
        # Partial match for guest name (case-insensitive)
        query["guest_name"] = {"$regex": guest_name, "$options": "i"}
    else:
        return {
            "error": "Please provide at least one of: confirmation number, guest name, email, or phone number"
        }
    
    # Find matching bookings
    bookings = await db.bookings.find(query).to_list(10)
    
    if not bookings:
        return {
            "found": False,
            "message": "No booking found with the provided information. Please double-check and try again."
        }
    
    # Format results
    results = []
    for booking in bookings:
        results.append({
            "confirmation_number": booking["confirmation_number"],
            "guest_name": booking["guest_name"],
            "guest_email": booking["guest_email"],
            "guest_phone": booking["guest_phone"],
            "room_number": booking["room_number"],
            "room_type": booking["room_type"],
            "floor": booking["floor"],
            "check_in_date": booking["check_in_date"],
            "check_out_date": booking["check_out_date"],
            "num_guests": booking["num_guests"],
            "price_per_night": booking["price_per_night"],
            "total_price": booking["total_price"],
            "status": booking["status"],
            "special_requests": booking.get("special_requests", [])
        })
    
    if len(results) == 1:
        return {
            "found": True,
            "booking": results[0]
        }
    else:
        return {
            "found": True,
            "message": f"Found {len(results)} bookings matching your search",
            "bookings": results
        }

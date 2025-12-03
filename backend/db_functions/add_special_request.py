from datetime import datetime
from db import db


async def add_special_request(
    confirmation_number: str = None,
    guest_name: str = None,
    guest_email: str = None,
    request: str = None
):
    """Add a special request to an existing booking.
    
    Args:
        confirmation_number: The booking confirmation number
        guest_name: Guest's name (alternative lookup)
        guest_email: Guest's email (alternative lookup)
        request: The special request to add (e.g., "late check-in", "extra pillows")
    
    Returns:
        Success confirmation or error message
    """
    # Validate request is provided
    if not request:
        return {
            "success": False,
            "error": "Please specify what special request you'd like to add."
        }
    
    # Build query to find the booking
    query = {}
    lookup_method = ""
    
    if confirmation_number:
        query["confirmation_number"] = {"$regex": confirmation_number, "$options": "i"}
        lookup_method = f"confirmation number {confirmation_number}"
    elif guest_email:
        query["guest_email"] = {"$regex": f"^{guest_email}$", "$options": "i"}
        lookup_method = f"email {guest_email}"
    elif guest_name:
        query["guest_name"] = {"$regex": guest_name, "$options": "i"}
        lookup_method = f"name {guest_name}"
    else:
        return {
            "success": False,
            "error": "Please provide a confirmation number, guest name, or email to find the booking."
        }
    
    # Find the booking first
    booking = await db.bookings.find_one(query)
    
    if not booking:
        return {
            "success": False,
            "error": f"No booking found with {lookup_method}. Please verify the information."
        }
    
    # Check if request already exists
    existing_requests = booking.get("special_requests", [])
    if request.lower() in [r.lower() for r in existing_requests]:
        return {
            "success": True,
            "message": f"'{request}' is already noted on your reservation.",
            "confirmation_number": booking["confirmation_number"],
            "guest_name": booking["guest_name"],
            "all_requests": existing_requests
        }
    
    # Add the special request
    result = await db.bookings.update_one(
        {"_id": booking["_id"]},
        {
            "$push": {"special_requests": request},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    if result.modified_count > 0:
        updated_requests = existing_requests + [request]
        return {
            "success": True,
            "message": f"I've added '{request}' to your reservation.",
            "confirmation_number": booking["confirmation_number"],
            "guest_name": booking["guest_name"],
            "all_requests": updated_requests
        }
    else:
        return {
            "success": False,
            "error": "Something went wrong while updating the booking. Please try again."
        }

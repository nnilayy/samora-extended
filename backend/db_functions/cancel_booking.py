"""
Cancel an existing booking in the hotel database.
"""

from datetime import datetime
from db import db


async def cancel_booking(
    confirmation_number: str = None,
    guest_name: str = None,
    guest_email: str = None
) -> dict:
    """
    Cancel an existing booking.
    
    Args:
        confirmation_number: The booking confirmation number
        guest_name: Guest's name (alternative lookup)
        guest_email: Guest's email (alternative lookup)
    
    Returns:
        dict with cancellation status and details
    """
    bookings = db["bookings"]
    
    # Build query based on provided parameters
    query = {}
    
    if confirmation_number:
        query["confirmation_number"] = confirmation_number.upper()
    elif guest_email:
        query["guest_email"] = guest_email.lower()
    elif guest_name:
        # Case-insensitive partial match
        query["guest_name"] = {"$regex": guest_name, "$options": "i"}
    else:
        return {
            "success": False,
            "error": "Please provide a confirmation number, name, or email to find the booking."
        }
    
    # Find the booking first
    booking = await bookings.find_one(query)
    
    if not booking:
        return {
            "success": False,
            "error": "No booking found with the provided information."
        }
    
    # Check if it's a past booking
    check_in_date = datetime.strptime(booking["check_in_date"], "%Y-%m-%d")
    if check_in_date.date() < datetime.now().date():
        return {
            "success": False,
            "error": "Cannot cancel a booking for a past date.",
            "booking": {
                "confirmation_number": booking["confirmation_number"],
                "check_in_date": booking["check_in_date"],
                "status": booking["status"]
            }
        }
    
    # Store booking details before deletion
    cancelled_booking = {
        "confirmation_number": booking["confirmation_number"],
        "guest_name": booking["guest_name"],
        "room_number": booking["room_number"],
        "room_type": booking["room_type"],
        "check_in_date": booking["check_in_date"],
        "check_out_date": booking["check_out_date"]
    }
    
    # Delete the booking
    result = await bookings.delete_one({"_id": booking["_id"]})
    
    if result.deleted_count == 1:
        return {
            "success": True,
            "message": "Booking has been successfully cancelled and removed.",
            "cancelled_booking": cancelled_booking
        }
    else:
        return {
            "success": False,
            "error": "Failed to cancel booking. Please try again."
        }

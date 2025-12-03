"""
Check room availability for given dates.
"""

from datetime import datetime
from db import db


async def check_availability(
    check_in_date: str,
    check_out_date: str,
    room_type: str = None,
    num_guests: int = None
) -> dict:
    """
    Check available rooms for the given date range.
    
    Args:
        check_in_date: Check-in date (YYYY-MM-DD format)
        check_out_date: Check-out date (YYYY-MM-DD format)
        room_type: Optional - filter by room type (standard, deluxe, suite)
        num_guests: Optional - filter by rooms that can accommodate this many guests
    
    Returns:
        dict with availability information
    """
    rooms = db["rooms"]
    bookings = db["bookings"]
    
    # Validate dates
    try:
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
    except ValueError:
        return {
            "success": False,
            "error": "Invalid date format. Please use YYYY-MM-DD format."
        }
    
    # Check dates are valid
    if check_in >= check_out:
        return {
            "success": False,
            "error": "Check-out date must be after check-in date."
        }
    
    if check_in.date() < datetime.now().date():
        return {
            "success": False,
            "error": "Check-in date cannot be in the past."
        }
    
    # Room capacity by type
    room_capacity = {
        "standard": 2,
        "deluxe": 3,
        "suite": 4
    }
    
    # Build room query
    room_query = {}
    if room_type:
        room_query["room_type"] = room_type.lower()
    
    # Filter by guest capacity if specified
    if num_guests:
        suitable_types = [t for t, cap in room_capacity.items() if cap >= num_guests]
        if not suitable_types:
            return {
                "success": False,
                "error": f"No room type can accommodate {num_guests} guests. Maximum capacity is 4 guests (suite)."
            }
        if room_type and room_type.lower() not in suitable_types:
            return {
                "success": False,
                "error": f"A {room_type} room can only accommodate {room_capacity.get(room_type.lower(), 2)} guests. You need {num_guests}."
            }
        if not room_type:
            room_query["room_type"] = {"$in": suitable_types}
    
    # Get all rooms matching criteria
    all_rooms = await rooms.find(room_query).to_list(length=None)
    
    if not all_rooms:
        return {
            "success": False,
            "error": f"No rooms found matching your criteria."
        }
    
    # Find rooms that are booked during the requested period
    # A room is unavailable if there's any booking that overlaps with requested dates
    booked_rooms_cursor = bookings.find({
        "$and": [
            {"check_in_date": {"$lt": check_out_date}},  # Booking starts before our checkout
            {"check_out_date": {"$gt": check_in_date}}   # Booking ends after our checkin
        ]
    })
    
    booked_room_numbers = set()
    async for booking in booked_rooms_cursor:
        booked_room_numbers.add(booking["room_number"])
    
    # Filter out booked rooms
    available_rooms = [r for r in all_rooms if r["room_number"] not in booked_room_numbers]
    
    if not available_rooms:
        return {
            "success": True,
            "available": False,
            "message": f"Sorry, no rooms are available from {check_in_date} to {check_out_date}.",
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "nights": (check_out - check_in).days
        }
    
    # Count available rooms by type
    availability_by_type = {}
    for room in available_rooms:
        rtype = room["room_type"]
        if rtype not in availability_by_type:
            availability_by_type[rtype] = {
                "count": 0,
                "price_per_night": room["price_per_night"],
                "max_guests": room_capacity.get(rtype, 2)
            }
        availability_by_type[rtype]["count"] += 1
    
    # Calculate nights and totals
    nights = (check_out - check_in).days
    
    # Build summary
    summary = []
    for rtype, info in availability_by_type.items():
        total = info["price_per_night"] * nights
        summary.append({
            "room_type": rtype,
            "available_count": info["count"],
            "price_per_night": info["price_per_night"],
            "total_price": total,
            "max_guests": info["max_guests"]
        })
    
    # Sort by price
    summary.sort(key=lambda x: x["price_per_night"])
    
    return {
        "success": True,
        "available": True,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "nights": nights,
        "room_options": summary,
        "total_available_rooms": len(available_rooms)
    }

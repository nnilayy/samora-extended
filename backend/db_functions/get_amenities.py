from db import db


async def get_amenities(room_type: str):
    """Get amenities for a specific room type.
    
    Args:
        room_type: Required - "standard", "deluxe", or "suite"
    """
    if not room_type:
        return {"error": "Please specify a room type: standard, deluxe, or suite"}
    
    room = await db.rooms.find_one({"room_type": room_type})
    
    if room:
        return {
            "room_type": room["room_type"],
            "amenities": room["amenities"]
        }
    else:
        return {"error": f"Room type '{room_type}' not found"}

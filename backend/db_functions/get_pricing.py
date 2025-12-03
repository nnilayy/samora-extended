from db import db


async def get_pricing(room_type: str = None):
    """Get pricing for all room types or a specific type.
    
    Args:
        room_type: Optional - "standard", "deluxe", or "suite"
    """
    if room_type:
        # Get price for specific room type
        room = await db.rooms.find_one({"room_type": room_type})
        if room:
            return {
                "room_type": room["room_type"],
                "price_per_night": room["price_per_night"],
                "capacity": room["capacity"]
            }
        else:
            return {"error": f"Room type '{room_type}' not found"}
    else:
        # Get all room types with prices
        pipeline = [
            {"$group": {
                "_id": "$room_type",
                "price_per_night": {"$first": "$price_per_night"},
                "capacity": {"$first": "$capacity"}
            }}
        ]
        rooms = await db.rooms.aggregate(pipeline).to_list(10)
        return {
            "pricing": [
                {
                    "room_type": r["_id"],
                    "price_per_night": r["price_per_night"],
                    "capacity": r["capacity"]
                } for r in rooms
            ]
        }

import random
from datetime import datetime
from db import db
from pipecat.services.llm_service import FunctionCallParams


async def book_room(
    params: FunctionCallParams,
    guest_name: str,
    guest_phone: str,
    guest_email: str,
    room_type: str,
    check_in_date: str,
    check_out_date: str,
    num_guests: int = 1,
    special_requests: list[str] = None,
):
    """Create a new room reservation.

    Use this ONLY after confirming all details with the guest: name, phone, email, room type,
    dates, and number of guests. Do NOT call this until you have collected all required information
    through the conversation.

    Args:
        guest_name: Full name of the guest.
        guest_phone: Guest's phone number.
        guest_email: Guest's email address.
        room_type: Type of room to book (standard, deluxe, suite).
        check_in_date: Check-in date in YYYY-MM-DD format.
        check_out_date: Check-out date in YYYY-MM-DD format.
        num_guests: Number of guests staying.
        special_requests: Optional list of special requests.
    """
    rooms = db["rooms"]
    bookings = db["bookings"]

    # Validate room type
    room_type = room_type.lower()
    if room_type not in ["standard", "deluxe", "suite"]:
        await params.result_callback(
            {
                "success": False,
                "error": f"Invalid room type '{room_type}'. Choose from: standard, deluxe, or suite.",
            }
        )
        return

    # Validate dates
    try:
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
    except ValueError:
        await params.result_callback(
            {
                "success": False,
                "error": "Invalid date format. Please use YYYY-MM-DD format.",
            }
        )
        return

    if check_in >= check_out:
        await params.result_callback(
            {"success": False, "error": "Check-out date must be after check-in date."}
        )
        return

    if check_in.date() < datetime.now().date():
        await params.result_callback(
            {"success": False, "error": "Check-in date cannot be in the past."}
        )
        return

    # Room capacity check
    room_capacity = {"standard": 2, "deluxe": 3, "suite": 4}
    max_guests = room_capacity.get(room_type, 2)

    if num_guests > max_guests:
        await params.result_callback(
            {
                "success": False,
                "error": f"A {room_type} room can only accommodate {max_guests} guests. You requested {num_guests}.",
            }
        )
        return

    # Get all rooms of the requested type
    all_rooms = await rooms.find({"room_type": room_type}).to_list(length=None)

    if not all_rooms:
        await params.result_callback(
            {"success": False, "error": f"No {room_type} rooms exist in our system."}
        )
        return

    # Find rooms that are already booked during the requested period
    booked_rooms_cursor = bookings.find(
        {
            "room_type": room_type,
            "$and": [
                {"check_in_date": {"$lt": check_out_date}},
                {"check_out_date": {"$gt": check_in_date}},
            ],
        }
    )

    booked_room_numbers = set()
    async for booking in booked_rooms_cursor:
        booked_room_numbers.add(booking["room_number"])

    # Find available rooms
    available_rooms = [
        r for r in all_rooms if r["room_number"] not in booked_room_numbers
    ]

    if not available_rooms:
        await params.result_callback(
            {
                "success": False,
                "error": f"Sorry, no {room_type} rooms are available for those dates. Please try different dates or a different room type.",
            }
        )
        return

    # Select a random available room
    selected_room = random.choice(available_rooms)

    # Calculate pricing
    nights = (check_out - check_in).days
    price_per_night = selected_room["price_per_night"]
    total_price = price_per_night * nights

    # Generate confirmation number
    # Get the highest existing confirmation number to increment
    last_booking = await bookings.find_one(
        {"confirmation_number": {"$regex": "^GV-2025-"}},
        sort=[("confirmation_number", -1)],
    )

    if last_booking:
        last_num = int(last_booking["confirmation_number"].split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1001

    confirmation_number = f"GV-2025-{new_num:06d}"

    # Create the booking document
    booking_doc = {
        "confirmation_number": confirmation_number,
        "guest_name": guest_name,
        "guest_phone": guest_phone,
        "guest_email": guest_email.lower(),
        "room_number": selected_room["room_number"],
        "room_type": room_type,
        "floor": selected_room["floor"],
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "num_guests": num_guests,
        "price_per_night": price_per_night,
        "total_price": total_price,
        "status": "confirmed",
        "special_requests": special_requests or [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    # Insert the booking
    insert_result = await bookings.insert_one(booking_doc)

    if insert_result.inserted_id:
        await params.result_callback(
            {
                "success": True,
                "message": "Booking confirmed successfully!",
                "booking": {
                    "confirmation_number": confirmation_number,
                    "guest_name": guest_name,
                    "room_type": room_type,
                    "room_number": selected_room["room_number"],
                    "floor": selected_room["floor"],
                    "check_in_date": check_in_date,
                    "check_out_date": check_out_date,
                    "nights": nights,
                    "num_guests": num_guests,
                    "price_per_night": price_per_night,
                    "total_price": total_price,
                    "special_requests": special_requests or [],
                },
            }
        )
    else:
        await params.result_callback(
            {"success": False, "error": "Failed to create booking. Please try again."}
        )

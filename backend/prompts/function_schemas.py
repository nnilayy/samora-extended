#
# Function Schemas - LLM function definitions for Pipecat
#

from pipecat.adapters.schemas.function_schema import FunctionSchema

from .function_descriptions import (
    HOLD_FUNCTION_DESCRIPTION,
    END_CALL_FUNCTION_DESCRIPTION,
    GET_PRICING_DESCRIPTION,
    GET_AMENITIES_DESCRIPTION,
    LOOKUP_BOOKING_DESCRIPTION,
    ADD_SPECIAL_REQUEST_DESCRIPTION,
    CANCEL_BOOKING_DESCRIPTION,
    CHECK_AVAILABILITY_DESCRIPTION,
    BOOK_ROOM_DESCRIPTION,
    UPDATE_BOOKING_DESCRIPTION,
)


# ============ CONTROL FUNCTIONS ============

hold_function = FunctionSchema(
    name="put_on_hold",
    description=HOLD_FUNCTION_DESCRIPTION,
    properties={},
    required=[]
)

end_call_function = FunctionSchema(
    name="end_call",
    description=END_CALL_FUNCTION_DESCRIPTION,
    properties={},
    required=[]
)


# ============ HOTEL BOOKING FUNCTIONS ============

get_pricing_function = FunctionSchema(
    name="get_pricing",
    description=GET_PRICING_DESCRIPTION,
    properties={
        "room_type": {
            "type": "string",
            "enum": ["standard", "deluxe", "suite"],
            "description": "The room type to get pricing for. Optional - omit to get all room prices."
        }
    },
    required=[]
)

get_amenities_function = FunctionSchema(
    name="get_amenities",
    description=GET_AMENITIES_DESCRIPTION,
    properties={
        "room_type": {
            "type": "string",
            "enum": ["standard", "deluxe", "suite"],
            "description": "The room type to get amenities for."
        }
    },
    required=["room_type"]
)

lookup_booking_function = FunctionSchema(
    name="lookup_booking",
    description=LOOKUP_BOOKING_DESCRIPTION,
    properties={
        "confirmation_number": {
            "type": "string",
            "description": "The booking confirmation number (e.g., GV-2025-001001)"
        },
        "guest_name": {
            "type": "string",
            "description": "The guest's full or partial name"
        },
        "guest_email": {
            "type": "string",
            "description": "The guest's email address"
        },
        "guest_phone": {
            "type": "string",
            "description": "The guest's phone number"
        }
    },
    required=[]
)

add_special_request_function = FunctionSchema(
    name="add_special_request",
    description=ADD_SPECIAL_REQUEST_DESCRIPTION,
    properties={
        "confirmation_number": {
            "type": "string",
            "description": "The booking confirmation number"
        },
        "guest_name": {
            "type": "string",
            "description": "The guest's name (alternative to confirmation number)"
        },
        "guest_email": {
            "type": "string",
            "description": "The guest's email (alternative to confirmation number)"
        },
        "request": {
            "type": "string",
            "description": "The special request to add (e.g., 'late check-in', 'extra pillows', 'baby crib')"
        }
    },
    required=["request"]
)

cancel_booking_function = FunctionSchema(
    name="cancel_booking",
    description=CANCEL_BOOKING_DESCRIPTION,
    properties={
        "confirmation_number": {
            "type": "string",
            "description": "The booking confirmation number"
        },
        "guest_name": {
            "type": "string",
            "description": "The guest's name (alternative to confirmation number)"
        },
        "guest_email": {
            "type": "string",
            "description": "The guest's email (alternative to confirmation number)"
        }
    },
    required=[]
)

check_availability_function = FunctionSchema(
    name="check_availability",
    description=CHECK_AVAILABILITY_DESCRIPTION,
    properties={
        "check_in_date": {
            "type": "string",
            "description": "Check-in date in YYYY-MM-DD format (e.g., 2025-12-15)"
        },
        "check_out_date": {
            "type": "string",
            "description": "Check-out date in YYYY-MM-DD format (e.g., 2025-12-18)"
        },
        "room_type": {
            "type": "string",
            "enum": ["standard", "deluxe", "suite"],
            "description": "Optional - filter by specific room type"
        },
        "num_guests": {
            "type": "integer",
            "description": "Optional - number of guests to accommodate"
        }
    },
    required=["check_in_date", "check_out_date"]
)

book_room_function = FunctionSchema(
    name="book_room",
    description=BOOK_ROOM_DESCRIPTION,
    properties={
        "guest_name": {
            "type": "string",
            "description": "Full name of the guest"
        },
        "guest_phone": {
            "type": "string",
            "description": "Guest's phone number"
        },
        "guest_email": {
            "type": "string",
            "description": "Guest's email address"
        },
        "room_type": {
            "type": "string",
            "enum": ["standard", "deluxe", "suite"],
            "description": "Type of room to book"
        },
        "check_in_date": {
            "type": "string",
            "description": "Check-in date in YYYY-MM-DD format"
        },
        "check_out_date": {
            "type": "string",
            "description": "Check-out date in YYYY-MM-DD format"
        },
        "num_guests": {
            "type": "integer",
            "description": "Number of guests staying"
        },
        "special_requests": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional list of special requests"
        }
    },
    required=["guest_name", "guest_phone", "guest_email", "room_type", "check_in_date", "check_out_date", "num_guests"]
)

update_booking_function = FunctionSchema(
    name="update_booking",
    description=UPDATE_BOOKING_DESCRIPTION,
    properties={
        "confirmation_number": {
            "type": "string",
            "description": "The booking confirmation number"
        },
        "guest_name": {
            "type": "string",
            "description": "Guest's name (alternative to confirmation number)"
        },
        "guest_email": {
            "type": "string",
            "description": "Guest's email (alternative to confirmation number)"
        },
        "new_check_in_date": {
            "type": "string",
            "description": "New check-in date in YYYY-MM-DD format"
        },
        "new_check_out_date": {
            "type": "string",
            "description": "New check-out date in YYYY-MM-DD format"
        },
        "new_room_type": {
            "type": "string",
            "enum": ["standard", "deluxe", "suite"],
            "description": "New room type"
        },
        "new_num_guests": {
            "type": "integer",
            "description": "New number of guests"
        }
    },
    required=[]
)

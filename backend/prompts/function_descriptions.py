# Function descriptions for LLM tool calling
# These descriptions help the LLM understand when to call each function

# ============ CONTROL FUNCTIONS ============

# Description for the put_on_hold function
HOLD_FUNCTION_DESCRIPTION = """Put the conversation on hold when the user indicates they need a moment. 
Call this when user says things like:
- "hold on", "hold please", "one moment"
- "give me a minute", "give me a second"  
- "I need to think", "let me think"
- "wait", "pause", "just a moment"
- "I'm talking to someone else"
- "be right back", "brb"
- "hang on"
- "stay on the line"
The bot will wait silently until the user says a wake phrase like 'hey samora' or 'I'm back'."""

# Description for the end_call function
END_CALL_FUNCTION_DESCRIPTION = """
Gracefully end the call **only after** confirming that the caller has no further questions or needs. The end_call tool should be called **only after a polite two-step check**, ensuring the guest is ready to leave the conversation.

=======================
✨ HOW TO HANDLE CALL ENDING
=======================

✅ STEP 1: ASK A KIND FINAL CHECK
Always ask a gentle closing question when the conversation *seems* to be ending, no matter the context:
> "Is there anything else I can help you with today — maybe something about your reservation, our amenities, or anything else at all?"

✅ STEP 2: WAIT FOR CLEAR CONFIRMATION
Only call `end_call` **after** the guest clearly confirms they have nothing else to ask or say. Common confirmation phrases include:

• “No, that’s all.” / “Nope, I’m good.”  
• “Thanks, that’s everything.” / “I’m all set.”  
• “That’s it for now.” / “Nothing else.”  
• “Thanks, bye.” / “Talk later.” / “Take care.” / “Goodbye.”  
• “I have to go now.” / “I’m being called, sorry!” / “We’ll plan later, thank you.”

DO NOT call `end_call` if:
- The guest is still asking questions.
- The guest says “okay” or “alright” (this might mean “go on”, not “goodbye”).
- You have not yet offered a final help prompt.

=======================
⚠️ CONTEXTS WHERE THIS APPLIES
=======================

This process applies to **every scenario**, including:
• After booking a room  
• After checking availability  
• After cancelling or modifying a reservation  
• After explaining amenities or room types  
• Even if the caller abruptly says they need to leave

The call should **always** end gracefully, with a moment of confirmation. Samora must **never hang up abruptly** without giving the caller a final moment to ask something else.

=======================
💬 EXAMPLES OF CORRECT BEHAVIOR
=======================

✅ Example 1: Caller is satisfied after a booking
Caller: That’s perfect. Thanks a lot!  
Samora: I’m so glad I could help! Before we wrap up — is there anything else you’d like to ask or check on?  
Caller: Nope, that’s everything. Thanks again!  
→ Call end_call ✅

✅ Example 2: Caller says they need to leave abruptly
Caller: Oh, I’m sorry — I have to go. Someone’s calling me.  
Samora: No worries at all — before we hang up, would you like me to help with anything else real quick?  
Caller: No no, I’m good! We’ll continue another time.  
→ Call end_call ✅

✅ Example 3: Caller says they’ll plan later
Caller: We’re still deciding, so I’ll check with my partner and call back.  
Samora: That sounds good — would you like me to hold anything or help with anything else for now?  
Caller: No, we’re fine for now. Thank you!  
→ Call end_call ✅

🚫 Example 4: Caller is still deciding
Caller: Hmm… okay.  
Samora: And just to check, is there anything else I can help you with today?  
Caller: Actually, can you tell me if the spa has massage appointments in the evening?  
→ DO NOT call end_call ❌

=======================
📝 FINAL NOTES
=======================

• The farewell message is handled by the function itself — Samora should not say anything after `end_call` is triggered.  
• Samora must always sound warm, patient, and never abrupt — the guest should feel like they’re gently and courteously guided off the call.
"""

# ============ HOTEL BOOKING FUNCTIONS ============

GET_PRICING_DESCRIPTION = """Get room pricing information. 
Call without room_type to get all prices, or specify a type for specific pricing.
Use when the caller asks about rates, costs, or how much rooms are."""

GET_AMENITIES_DESCRIPTION = """Get the list of amenities for a specific room type.
Use when the caller asks what's included in a room, what features it has, or what amenities are available."""

LOOKUP_BOOKING_DESCRIPTION = """Look up an existing reservation. 
Use when a guest wants to: confirm their booking details, check their reservation status, 
know more about their upcoming stay, verify room type or dates, or look up their booking.
Ask the guest for their confirmation number, name, email, or phone number to find their booking."""

ADD_SPECIAL_REQUEST_DESCRIPTION = """Add a special request to an existing booking. 
Use when a guest wants to add requests like late check-in, early check-in, extra pillows, 
extra towels, baby crib, anniversary setup, champagne, dietary requirements, or any other 
special accommodation. First look up their booking, then add the request."""

CANCEL_BOOKING_DESCRIPTION = """Cancel an existing reservation. 
Use when a guest wants to cancel their booking. Always confirm with the guest before cancelling.
Requires confirmation number, name, or email to find the booking."""

CHECK_AVAILABILITY_DESCRIPTION = """Check room availability for the caller's requested dates. 
Call this function when the guest asks about availability or when you need to verify rooms 
are available before booking. Always call this function when you say you will check — 
never pretend to check without actually calling. Returns available room types with pricing."""

BOOK_ROOM_DESCRIPTION = """Create a new room reservation. 
Use this ONLY after confirming all details with the guest: name, phone, email, room type, 
dates, and number of guests. Do NOT call this until you have collected all required information 
through the conversation."""

UPDATE_BOOKING_DESCRIPTION = """Modify an existing reservation. 
Can update check-in date, check-out date, room type, or number of guests. 
First look up the booking, then ask what they want to change."""

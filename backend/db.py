import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))

# Get the hotel_db database
db = client["hotel_db"]

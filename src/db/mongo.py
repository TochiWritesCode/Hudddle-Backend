from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import pymongo.errors
from datetime import datetime, timedelta
from src.config import Config
import logging

JTI_EXPIRY = 3600

class MongoBlocklist:
    def __init__(self):
        self.mongo_client: AsyncIOMotorClient | None = None
        self.blocklist_collection: AsyncIOMotorDatabase | None = None

    async def initialize(self):
        try:
            self.mongo_client = AsyncIOMotorClient(Config.MONGO_URI)
            db = self.mongo_client[Config.MONGO_DB_NAME]
            self.blocklist_collection = db["token_blocklist"]
            await self.mongo_client.admin.command('ping')
            logging.info("Successfully connected to MongoDB")
            await self._create_ttl_index()
        except pymongo.errors.ConnectionFailure as e:
            logging.error(f"MongoDB connection failed: {e}")
            raise
        except Exception as e:
            logging.error(f"Error initializing MongoDB: {e}")
            raise

    async def add_jti_to_blocklist(self, jti: str) -> None:
        try:
            expiry_time = datetime.utcnow() + timedelta(seconds=JTI_EXPIRY)
            await self.blocklist_collection.insert_one({
                "jti": jti,
                "expiry": expiry_time
            })
            logging.info(f"Added {jti} to blocklist with expiry at {expiry_time}")
        except Exception as e:
            logging.error(f"Error adding to blocklist: {e}")

    async def token_in_blocklist(self, jti: str) -> bool:
        try:
            token = await self.blocklist_collection.find_one({
                "jti": jti,
                "expiry": {"$gt": datetime.utcnow()}
            })
            return token is not None
        except Exception as e:
            logging.error(f"Error checking blocklist: {e}")
            return False

    async def _create_ttl_index(self):
        try:
            await self.blocklist_collection.create_index("expiry", expireAfterSeconds=0)
            logging.info("TTL index created on 'expiry' field")
        except Exception as e:
            logging.error(f"Error creating TTL index: {e}")

    async def cleanup_expired_tokens(self):
        try:
            result = await self.blocklist_collection.delete_many({
                "expiry": {"$lte": datetime.utcnow()}
            })
            logging.info(f"Cleaned up {result.deleted_count} expired tokens")
        except Exception as e:
            logging.error(f"Error cleaning up expired tokens: {e}")

# Usage:
mongo_blocklist = MongoBlocklist()

async def initialize_blocklist():
    await mongo_blocklist.initialize()

async def add_jti_to_blocklist(jti:str):
    await mongo_blocklist.add_jti_to_blocklist(jti)

async def token_in_blocklist(jti: str):
    return await mongo_blocklist.token_in_blocklist(jti)

async def cleanup_expired_tokens():
    await mongo_blocklist.cleanup_expired_tokens()
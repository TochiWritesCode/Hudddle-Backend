from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

MONGO_URI = "mongodb+srv://hudddleioo:uGfzUvrvz6whMNln@huddlecluster.mjj7d.mongodb.net/?retryWrites=true&w=majority&appName=HuddleCluster"
DATABASE_NAME = "huddle"

client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]
tasks_collection = db["tasks"]

# Helper function to convert MongoDB documents
def task_serializer(task) -> dict:
    return {
        "id": str(task["_id"]),
        "name": task["name"],
        "duration": task["duration"],
        "deadline": task["deadline"],
        "tool": task["tool"],
        "status": task["status"],
        "workroom": task["workroom"],
        "assigned_to": task["assigned_to"],
        "points": task.get("points", 10)
    }

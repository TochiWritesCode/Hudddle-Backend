from fastapi import APIRouter, HTTPException
from database import tasks_collection, task_serializer
from schemas import TaskCreate, TaskUpdate
from bson import ObjectId

router = APIRouter()

# Create Task
@router.post("/tasks/")
async def create_task(task: TaskCreate):
    task_dict = task.model_dump()
    task_dict["status"] = "not_started"
    task_dict["points"] = 10  # Default points

    new_task = await tasks_collection.insert_one(task_dict)
    created_task = await tasks_collection.find_one({"_id": new_task.inserted_id})
    
    return {"message": "Task created successfully", "task": task_serializer(created_task)}

# Get All Tasks
@router.get("/tasks/")
async def get_tasks():
    tasks = await tasks_collection.find().to_list(length=100)
    return {"tasks": [task_serializer(task) for task in tasks]}

# Get Task by ID
@router.get("/tasks/{task_id}/")
async def get_task(task_id: str):
    task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_serializer(task)

# Update Task
@router.put("/tasks/{task_id}/")
async def update_task(task_id: str, task_update: TaskUpdate):
    update_data = {k: v for k, v in task_update.model_dump(exclude_unset=True).items()}
    
    task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await tasks_collection.update_one({"_id": ObjectId(task_id)}, {"$set": update_data})
    updated_task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
    
    return {"message": "Task updated successfully", "task": task_serializer(updated_task)}

# Delete Task
@router.delete("/tasks/{task_id}/")
async def delete_task(task_id: str):
    task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await tasks_collection.delete_one({"_id": ObjectId(task_id)})
    return {"message": "Task deleted successfully"}

# Reassign Task
@router.put("/tasks/{task_id}/reassign/")
async def reassign_task(task_id: str, new_assigned_to: str):
    task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await tasks_collection.update_one({"_id": ObjectId(task_id)}, {"$set": {"assigned_to": new_assigned_to}})
    return {"message": f"Task reassigned to {new_assigned_to}"}

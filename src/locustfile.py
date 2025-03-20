# On terminal 1 run main app on terminal
# On terminal 2 run (locust -f locustfile.py --host http://localhost:8000/api/v1)

from locust import HttpUser, task, between
import json
import uuid
import random

class UserTasks(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login a user and store the access token."""
        self.email = f"testuser{random.randint(1, 10000)}@example.com"
        self.password = "password123"
        self.username = f"testuser{random.randint(1, 10000)}"

        # Signup a new user, if needed.
        signup_data = {
            "email": self.email,
            "password": self.password,
            "username": self.username,
        }
        self.client.post("/auth/signup", json=signup_data)

        # Login and get the token
        login_data = {
            "email": self.email,
            "password": self.password,
        }
        response = self.client.post("/auth/login", json=login_data)
        if response.status_code == 200:
            self.access_token = response.json()["access token"]
            self.user_id = response.json()["user"]["uid"]
        else:
            print(f"Login failed: {response.text}")

        # Create a workroom for the user.
        workroom_data = {
            "name": f"Workroom {random.randint(1, 100)}",
            "description": "Test workroom",
        }
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.client.post("/workrooms", json=workroom_data, headers=headers)
        if response.status_code == 201:
            self.workroom_id = response.json()["id"]
        else:
            print(f"Workroom creation failed: {response.text}")

    @task
    def get_user_profile(self):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        self.client.get("/auth/me", headers=headers)

    @task
    def create_and_update_task(self):
        task_data = {
            "title": f"Task {random.randint(1, 100)}",
            "description": "Test task",
            "workroom_id": self.workroom_id,
        }
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.client.post("/tasks", json=task_data, headers=headers)
        if response.status_code == 200:
            task_id = response.json()["id"]
            update_data = {
                "status": "COMPLETED",
            }
            self.client.put(f"/tasks/{task_id}", json=update_data, headers=headers)

    @task
    def get_workroom_members(self):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        self.client.get(f"/workrooms/{self.workroom_id}/members", headers=headers)

    @task
    def update_user_profile(self):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        update_data = {
            "first_name": f"FirstName {random.randint(1, 100)}",
            "last_name": f"LastName {random.randint(1, 100)}"
        }
        self.client.put("/auth/update-profile", json=update_data, headers=headers)

    @task
    def create_workroom(self):
        workroom_data = {
            "name": f"Workroom {random.randint(1, 100)}",
            "description": "Test workroom",
        }
        headers = {"Authorization": f"Bearer {self.access_token}"}
        self.client.post("/workrooms", json=workroom_data, headers=headers)
        
        
        
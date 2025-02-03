#from fastapi import FastAPI
#from tasks import router as task_router

#app = FastAPI()


#@app.get("/")


from pathlib import Path
import uvicorn
from fastapi import FastAPI
from tasks import router as task_router

app = FastAPI()

app.include_router(task_router)
@app.get("/")
def index():
    return {"index": "root"}

def home():
   return {"message": "Welcome to the Huddle Task API (MongoDB Version)"}

if __name__ == '__main__':

    uvicorn.run(f"{Path(__file__).stem}:app", host="127.0.0.1", port=8000, reload=True)

from typing import Union
import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse

from madsoft.routers import router

app = FastAPI()

@app.get("/")
def docs():
    return RedirectResponse("/docs")

@app.get("/r")
def redoc():
    return RedirectResponse("/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/memes", tags=["User management"])

if __name__ == "__main__":
    uvicorn.run("madsoft.main:app", host="0.0.0.0", port=8000, reload=True)

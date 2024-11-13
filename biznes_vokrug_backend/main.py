from typing import Union
import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse

from biznes_vokrug_backend.auth import get_current_user

from .routers import router

app = FastAPI(
    title="Your API",
    description="API documentation with authorization required",
    dependencies=[Depends(get_current_user)]
)

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

app.include_router(router, prefix="/api", tags=["User management"])

if __name__ == "__main__":
    uvicorn.run("biznes_vokrug_backend.main:app", host="0.0.0.0", port=8000, reload=True)

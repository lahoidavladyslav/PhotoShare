from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import auth

app = FastAPI(
    title="PhotoShare API",
    description="REST API application for sharing photos",
    version="1.0.0"
)

app.include_router(auth.router, prefix="/api")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to PhotoShare API"}
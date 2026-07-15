from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from routers import datasets, chat, auth, predictions, mcp

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="weatherBOT API",
    version="2.0.0",
    description="Edge AI Weather Intelligence Platform — Full MCP Architecture",
)

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to weatherBOT API v2.0",
        "architecture": "MCP Service Router + 6 Services + 3 Engines + 3 Managers + IoT + Standard MCP SDK",
    }

# Core routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# New routers (v2)
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(mcp.router, prefix="/api/mcp", tags=["mcp"])

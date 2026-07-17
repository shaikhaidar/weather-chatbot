from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from routers import datasets, chat, auth, predictions, mcp

# Create tables
Base.metadata.create_all(bind=engine)

# Auto-migrate SQLite columns for legacy databases
from sqlalchemy import text
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE datasets ADD COLUMN status VARCHAR DEFAULT 'COMPLETED'"))
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute(text("ALTER TABLE datasets ADD COLUMN error_message TEXT"))
        conn.commit()
    except Exception:
        pass

app = FastAPI(
    title="weatherBOT API",
    version="2.0.0",
    description="Edge AI Weather Intelligence Platform — Full MCP Architecture",
)

# Allow CORS for local development & network access (supports flexible IP/port hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="https?://.*",
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

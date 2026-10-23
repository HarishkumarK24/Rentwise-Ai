import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.database import engine, Base, SessionLocal
from backend.app.routers.api_router import router as api_router
from backend.app.mock_connectors.payment_connector import seed_mock_portal

# Ensure tables are created
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        seed_mock_portal(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="RentWise AI — Rent Receipt & HRA Proof Pack Agent API",
    description="Intelligent agent for HRA evidence collection, deterministic payment reconciliation, PAN compliance, PDF receipt generation, human approval gate, and post-upload verification.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes under /api
app.include_router(api_router, prefix="/api")

# Serve frontend build if present (Unified Single-Service Deployment)
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "app": "RentWise AI",
            "description": "Rent Receipt & HRA Proof Pack Agent API",
            "docs": "/docs",
            "api_base": "/api"
        }

from fastapi import FastAPI
from .auth_routes import router as auth_router
from .work_queue_routes import router as work_queue_router
from .pick_locations_routes import router as locations_router
from .warehouse_designer_routes import router as designer_router

app = FastAPI(
    title="VoicePicker API",
    description="Voice-driven Warehouse Management System API",
    version="1.0.0"
)

# Include routers
app.include_router(auth_router, tags=["Authentication & Workers"])
app.include_router(work_queue_router, tags=["Work Queue"])
app.include_router(locations_router, tags=["Pick Locations"])
app.include_router(designer_router, tags=["Warehouse Designer"])

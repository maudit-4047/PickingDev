from fastapi import FastAPI
from .auth_routes import router as auth_router

app = FastAPI()

# Include the authentication/worker router
app.include_router(auth_router)

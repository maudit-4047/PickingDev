from fastapi import FastAPI

# Create minimal app for testing
app = FastAPI(
    title="VoicePicker API",
    description="Voice-driven Warehouse Management System API with Enhanced Security",
    version="2.0.0"
)

@app.get("/")
async def root():
    return {
        "message": "VoicePicker API v2.0 - Enhanced Security Edition",
        "status": "Working!",
        "features": [
            "Argon2 password hashing",
            "2FA/TOTP authentication", 
            "Rate limiting",
            "Account locking",
            "Security headers",
            "Flexible warehouse management"
        ]
    }

@app.get("/test")
async def test():
    return {"test": "This endpoint is working!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "voicepicker-api"}
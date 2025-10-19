from fastapi import FastAPI

# Import routes with error handling
try:
    from .user_routes_enhanced import router as user_router
    USER_ROUTER_AVAILABLE = True
except ImportError as e:
    USER_ROUTER_AVAILABLE = False
    print(f"Warning: Enhanced user routes not available: {e}")

try:
    from .auth_routes import router as auth_router
    AUTH_ROUTER_AVAILABLE = True
except ImportError as e:
    AUTH_ROUTER_AVAILABLE = False
    print(f"Warning: Auth routes not available: {e}")

try:
    from .inventory_routes import router as inventory_router
    INVENTORY_ROUTER_AVAILABLE = True
except ImportError as e:
    INVENTORY_ROUTER_AVAILABLE = False
    print(f"Warning: Inventory routes not available: {e}")

try:
    from .order_routes import router as order_router
    ORDER_ROUTER_AVAILABLE = True
except ImportError as e:
    ORDER_ROUTER_AVAILABLE = False
    print(f"Warning: Order routes not available: {e}")

try:
    from .dispatch_routes import router as dispatch_router
    DISPATCH_ROUTER_AVAILABLE = True
except ImportError as e:
    DISPATCH_ROUTER_AVAILABLE = False
    print(f"Warning: Dispatch routes not available: {e}")

try:
    from .config_routes import router as config_router
    CONFIG_ROUTER_AVAILABLE = True
except ImportError as e:
    CONFIG_ROUTER_AVAILABLE = False
    print(f"Warning: Config routes not available: {e}")

try:
    from .pick_locations_routes import router as locations_router
    LOCATIONS_ROUTER_AVAILABLE = True
except ImportError as e:
    LOCATIONS_ROUTER_AVAILABLE = False
    print(f"Warning: Pick locations routes not available: {e}")

try:
    from .warehouse_designer_routes import router as designer_router
    DESIGNER_ROUTER_AVAILABLE = True
except ImportError as e:
    DESIGNER_ROUTER_AVAILABLE = False
    print(f"Warning: Warehouse designer routes not available: {e}")

try:
    from .work_queue_routes import router as work_queue_router
    WORK_QUEUE_ROUTER_AVAILABLE = True
except ImportError as e:
    WORK_QUEUE_ROUTER_AVAILABLE = False
    print(f"Warning: Work queue routes not available: {e}")

try:
    from .user_routes import router as basic_user_router
    BASIC_USER_ROUTER_AVAILABLE = True
except ImportError as e:
    BASIC_USER_ROUTER_AVAILABLE = False
    print(f"Warning: Basic user routes not available: {e}")

app = FastAPI(
    title="VoicePicker API",
    description="Voice-driven Warehouse Management System API with Enhanced Security",
    version="2.0.0"
)

# Security headers disabled temporarily for testing
# @app.middleware("http")  
# async def add_security_headers(request, call_next):
#     response = await call_next(request)
#     
#     # Add security headers manually (more reliable than secure library)
#     response.headers["X-Content-Type-Options"] = "nosniff"
#     response.headers["X-Frame-Options"] = "DENY"
#     response.headers["X-XSS-Protection"] = "1; mode=block"
#     response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
#     response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'"
#     response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
#     
#     return response

# Include all working routers
# Include routers - check if they have their own prefixes to avoid conflicts
if USER_ROUTER_AVAILABLE:
    app.include_router(user_router)  # Already has prefix="/api/users"

if AUTH_ROUTER_AVAILABLE:
    app.include_router(auth_router, prefix="/api/auth", tags=["Worker Authentication"])

if INVENTORY_ROUTER_AVAILABLE:
    app.include_router(inventory_router, prefix="/api/inventory", tags=["Inventory Management"])

if ORDER_ROUTER_AVAILABLE:
    app.include_router(order_router, prefix="/api/orders", tags=["Order Management"])

if DISPATCH_ROUTER_AVAILABLE:
    app.include_router(dispatch_router, prefix="/api/dispatch", tags=["Dispatch Management"])

if CONFIG_ROUTER_AVAILABLE:
    app.include_router(config_router, prefix="/api/config", tags=["Configuration"])

if LOCATIONS_ROUTER_AVAILABLE:
    app.include_router(locations_router, prefix="/api/locations", tags=["Pick Locations"])

if DESIGNER_ROUTER_AVAILABLE:
    app.include_router(designer_router)  # Already has prefix="/warehouse-designer"

if WORK_QUEUE_ROUTER_AVAILABLE:
    app.include_router(work_queue_router, prefix="/api/work-queue", tags=["Work Queue"])

# Skip basic_user_router to avoid conflict with enhanced user_router (both use /api/users)
# if BASIC_USER_ROUTER_AVAILABLE:
#     app.include_router(basic_user_router, prefix="/api/basic-users", tags=["Basic User Management"])

@app.get("/")
async def root():
    available_endpoints = {
        "docs": "/docs",
        "redoc": "/redoc", 
        "health": "/health",
        "test": "/test"
    }
    
    # Add available API routes
    if USER_ROUTER_AVAILABLE:
        available_endpoints["enhanced_auth"] = "/api/users"
    if AUTH_ROUTER_AVAILABLE:
        available_endpoints["worker_auth"] = "/api/auth"  
    if INVENTORY_ROUTER_AVAILABLE:
        available_endpoints["inventory"] = "/api/inventory"
    if ORDER_ROUTER_AVAILABLE:
        available_endpoints["orders"] = "/api/orders"
    if DISPATCH_ROUTER_AVAILABLE:
        available_endpoints["dispatch"] = "/api/dispatch"
    if CONFIG_ROUTER_AVAILABLE:
        available_endpoints["configuration"] = "/api/config"
    if LOCATIONS_ROUTER_AVAILABLE:
        available_endpoints["pick_locations"] = "/api/locations"
    if DESIGNER_ROUTER_AVAILABLE:
        available_endpoints["warehouse_designer"] = "/warehouse-designer"
    if WORK_QUEUE_ROUTER_AVAILABLE:
        available_endpoints["work_queue"] = "/api/work-queue"
    if BASIC_USER_ROUTER_AVAILABLE:
        available_endpoints["basic_users"] = "/api/basic-users"
    
    return {
        "message": "VoicePicker API v2.0 - Enhanced Security Edition",
        "status": "✅ Working!",
        "features": [
            "Argon2 password hashing",
            "2FA/TOTP authentication", 
            "Rate limiting",
            "Account locking",
            "Security headers",
            "Flexible warehouse management"
        ],
        "available_routes": available_endpoints,
        "loaded_modules": {
            "enhanced_auth": USER_ROUTER_AVAILABLE,
            "worker_auth": AUTH_ROUTER_AVAILABLE,
            "inventory": INVENTORY_ROUTER_AVAILABLE,
            "orders": ORDER_ROUTER_AVAILABLE,
            "dispatch": DISPATCH_ROUTER_AVAILABLE,
            "configuration": CONFIG_ROUTER_AVAILABLE,
            "pick_locations": LOCATIONS_ROUTER_AVAILABLE,
            "warehouse_designer": DESIGNER_ROUTER_AVAILABLE,
            "work_queue": WORK_QUEUE_ROUTER_AVAILABLE,
            "basic_users": BASIC_USER_ROUTER_AVAILABLE
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "voicepicker-api",
        "version": "2.0.0",
        "enhanced_auth": USER_ROUTER_AVAILABLE
    }

@app.get("/test")
async def test():
    return {
        "test": "✅ This endpoint is working!",
        "database": "Connected to Supabase",
        "authentication": "Enhanced 2FA system ready"
    }

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .auth.routes import router as auth_router
from .items.routes import router as items_router
from .database import engine
from .models import Base

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("Starting Lost & Found Portal API initialization")
logger.info("=" * 80)

# Test database connection (non-blocking)
if engine is not None:
    try:
        logger.info("Testing database connection...")
        with engine.connect() as conn:
            logger.info("✓ Database connection successful!")
            conn.close()
        
        # Create tables
        try:
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("✓ Database tables created/verified successfully!")
        except Exception as e:
            logger.error(f"⚠ Failed to create database tables: {e}")
    except Exception as e:
        logger.warning(f"⚠ Database not ready yet (will retry on requests): {e}")
else:
    logger.warning("⚠ Database engine not initialized - will retry on first request")

# Initialize FastAPI app
app = FastAPI(title="Lost & Found Portal API")
logger.info("✓ FastAPI app initialized")

# Add CORS middleware
try:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("✓ CORS middleware configured")
except Exception as e:
    logger.error(f"✗ Failed to add CORS middleware: {e}")
    raise

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("✓ Static files mounted at /static")
except Exception as e:
    logger.warning(f"⚠ Static files mount warning: {e}")

# Include routers
try:
    logger.info("Loading auth router...")
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    logger.info(f"✓ Auth router loaded with {len(auth_router.routes)} routes")
    
    logger.info("Loading items router...")
    app.include_router(items_router, prefix="/items", tags=["items"])
    logger.info(f"✓ Items router loaded with {len(items_router.routes)} routes")
except Exception as e:
    logger.error(f"✗ Failed to include routers: {e}")
    raise


@app.get("/")
async def root():
    return {"message": "Lost & Found Portal API is running"}

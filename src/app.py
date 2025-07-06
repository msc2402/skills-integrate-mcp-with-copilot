"""
High School Management System API

A FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
Now with persistent database storage and improved error handling!
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import os
import logging
from pathlib import Path
from .database import get_db, init_database, seed_initial_data, create_backup
from .models import Activity, User, activity_participants

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
    version="2.0.0"
)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        logger.info("Starting up Mergington High School API...")
        await init_database()
        await seed_initial_data()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # Continue startup even if seeding fails


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
async def get_activities(db: AsyncSession = Depends(get_db)):
    """Get all activities with their participants"""
    try:
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Activity).options(selectinload(Activity.participants))
        )
        activities = result.scalars().all()
        
        # Convert to the format expected by the frontend
        activities_dict = {}
        for activity in activities:
            activities_dict[activity.name] = {
                "description": activity.description,
                "schedule": activity.schedule,
                "max_participants": activity.max_participants,
                "participants": [user.email for user in activity.participants],
                "available_spots": activity.available_spots,
                "is_full": activity.is_full
            }
        
        return activities_dict
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving activities from database"
        )


@app.post("/activities/{activity_name}/signup")
async def signup_for_activity(activity_name: str, email: str, db: AsyncSession = Depends(get_db)):
    """Sign up a student for an activity"""
    try:
        from sqlalchemy.orm import selectinload
        # Get the activity with participants loaded
        result = await db.execute(
            select(Activity)
            .options(selectinload(Activity.participants))
            .where(Activity.name == activity_name)
        )
        activity = result.scalar_one_or_none()
        
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        # Check if activity is full before proceeding
        if activity.is_full:
            raise HTTPException(
                status_code=400,
                detail="Activity is full"
            )
        
        # Get or create the user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(email=email)
            db.add(user)
            await db.flush()  # Get the user ID
        
        # Check if user is already signed up
        if user in activity.participants:
            raise HTTPException(
                status_code=400,
                detail="Student is already signed up"
            )
        
        # Add user to activity
        activity.participants.append(user)
        await db.commit()
        
        logger.info(f"User {email} signed up for {activity_name}")
        return {"message": f"Signed up {email} for {activity_name}"}
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Integrity error in signup: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data integrity error - possibly invalid email format"
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error in signup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing signup request"
        )


@app.delete("/activities/{activity_name}/unregister")
async def unregister_from_activity(activity_name: str, email: str, db: AsyncSession = Depends(get_db)):
    """Unregister a student from an activity"""
    try:
        from sqlalchemy.orm import selectinload
        # Get the activity with participants loaded
        result = await db.execute(
            select(Activity)
            .options(selectinload(Activity.participants))
            .where(Activity.name == activity_name)
        )
        activity = result.scalar_one_or_none()
        
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        # Get the user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user or user not in activity.participants:
            raise HTTPException(
                status_code=400,
                detail="Student is not signed up for this activity"
            )
        
        # Remove user from activity
        activity.participants.remove(user)
        await db.commit()
        
        logger.info(f"User {email} unregistered from {activity_name}")
        return {"message": f"Unregistered {email} from {activity_name}"}
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error in unregister: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing unregister request"
        )


@app.get("/admin/backup")
async def create_database_backup():
    """Create a backup of the database (admin endpoint)"""
    try:
        backup_path = await create_backup()
        if backup_path:
            return {"message": "Backup created successfully", "backup_path": backup_path}
        else:
            return {"message": "Backup not available for this database type"}
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating database backup"
        )


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint to verify database connectivity"""
    try:
        # Simple query to test database connection
        result = await db.execute(select(Activity).limit(1))
        result.scalar_one_or_none()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )

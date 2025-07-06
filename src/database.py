"""
Database configuration and setup for the Mergington High School activities system.
"""

import os
import logging
import shutil
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from .models import Base

# Set up logging
logger = logging.getLogger(__name__)

# Database URL - use SQLite for development, can be changed for production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./mergington_activities.db")

# Database configuration with connection pooling
engine_kwargs = {
    "echo": os.getenv("DEBUG", "false").lower() == "true",  # Only echo in debug mode
}

# For SQLite, add connection pooling and WAL mode for better concurrency
if "sqlite" in DATABASE_URL:
    engine_kwargs.update({
        "poolclass": StaticPool,
        "connect_args": {
            "check_same_thread": False,
            "timeout": 20,
        },
        "pool_pre_ping": True,
        "pool_recycle": 300,
    })

# Create async engine with improved configuration
engine = create_async_engine(DATABASE_URL, **engine_kwargs)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_database():
    """Initialize the database and create tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def get_db():
    """Dependency to get database session with proper error handling"""
    session = None
    try:
        session = AsyncSessionLocal()
        yield session
    except Exception as e:
        if session:
            await session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        if session:
            await session.close()


async def create_backup():
    """Create a backup of the SQLite database"""
    try:
        if "sqlite" in DATABASE_URL:
            # Extract database path from URL
            db_path = DATABASE_URL.split("///")[-1]
            if db_path.startswith("./"):
                db_path = db_path[2:]
            
            db_file = Path(db_path)
            if db_file.exists():
                # Create backup with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = db_file.parent / f"{db_file.stem}_backup_{timestamp}{db_file.suffix}"
                
                shutil.copy2(db_file, backup_path)
                logger.info(f"Database backup created: {backup_path}")
                return str(backup_path)
            else:
                logger.warning("Database file not found for backup")
                return None
        else:
            logger.warning("Backup not implemented for non-SQLite databases")
            return None
    except Exception as e:
        logger.error(f"Failed to create database backup: {e}")
        raise


async def seed_initial_data():
    """Seed the database with initial activities data"""
    from .models import Activity, User, activity_participants
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        # Check if we already have data
        result = await session.execute(select(Activity))
        existing_activities = result.scalars().all()
        
        if existing_activities:
            return  # Data already exists
        
        # Create initial activities
        initial_activities = [
            {
                "name": "Chess Club",
                "description": "Learn strategies and compete in chess tournaments",
                "schedule": "Fridays, 3:30 PM - 5:00 PM",
                "max_participants": 12
            },
            {
                "name": "Programming Class",
                "description": "Learn programming fundamentals and build software projects",
                "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
                "max_participants": 20
            },
            {
                "name": "Gym Class",
                "description": "Physical education and sports activities",
                "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
                "max_participants": 30
            },
            {
                "name": "Soccer Team",
                "description": "Join the school soccer team and compete in matches",
                "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
                "max_participants": 22
            },
            {
                "name": "Basketball Team",
                "description": "Practice and play basketball with the school team",
                "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
                "max_participants": 15
            },
            {
                "name": "Art Club",
                "description": "Explore your creativity through painting and drawing",
                "schedule": "Thursdays, 3:30 PM - 5:00 PM",
                "max_participants": 15
            },
            {
                "name": "Drama Club",
                "description": "Act, direct, and produce plays and performances",
                "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
                "max_participants": 20
            },
            {
                "name": "Math Club",
                "description": "Solve challenging problems and participate in math competitions",
                "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
                "max_participants": 10
            },
            {
                "name": "Debate Team",
                "description": "Develop public speaking and argumentation skills",
                "schedule": "Fridays, 4:00 PM - 5:30 PM",
                "max_participants": 12
            }
        ]
        
        # Create activities
        for activity_data in initial_activities:
            activity = Activity(**activity_data)
            session.add(activity)
        
        # Create some initial users with existing enrollments
        initial_users_data = [
            ("michael@mergington.edu", "Chess Club"),
            ("daniel@mergington.edu", "Chess Club"),
            ("emma@mergington.edu", "Programming Class"),
            ("sophia@mergington.edu", "Programming Class"),
            ("john@mergington.edu", "Gym Class"),
            ("olivia@mergington.edu", "Gym Class"),
            ("liam@mergington.edu", "Soccer Team"),
            ("noah@mergington.edu", "Soccer Team"),
            ("ava@mergington.edu", "Basketball Team"),
            ("mia@mergington.edu", "Basketball Team"),
            ("amelia@mergington.edu", "Art Club"),
            ("harper@mergington.edu", "Art Club"),
            ("ella@mergington.edu", "Drama Club"),
            ("scarlett@mergington.edu", "Drama Club"),
            ("james@mergington.edu", "Math Club"),
            ("benjamin@mergington.edu", "Math Club"),
            ("charlotte@mergington.edu", "Debate Team"),
            ("henry@mergington.edu", "Debate Team")
        ]
        
        await session.commit()
        
        # Now add users and their enrollments
        for email, activity_name in initial_users_data:
            # Get or create user
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(email=email)
                session.add(user)
                await session.flush()  # Get the user ID
            
            # Get activity
            result = await session.execute(select(Activity).where(Activity.name == activity_name))
            activity = result.scalar_one_or_none()
            
            if activity:
                # Check if user is already enrolled (avoid duplicates)
                result = await session.execute(
                    select(User).join(activity_participants).join(Activity).where(
                        User.id == user.id,
                        Activity.id == activity.id
                    )
                )
                existing_enrollment = result.scalar_one_or_none()
                
                if not existing_enrollment:
                    activity.participants.append(user)
        
        await session.commit()

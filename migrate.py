#!/usr/bin/env python3
"""
Database migration script for the Mergington High School activities system.
This script helps migrate existing data when schema changes are made.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from src.database import init_database, seed_initial_data, AsyncSessionLocal, create_backup
from src.models import Activity, User, Base
from sqlalchemy import select, text


async def migrate_database():
    """Run database migrations"""
    print("🔄 Starting database migration...")
    
    try:
        # Create backup before migration
        print("📦 Creating backup before migration...")
        backup_path = await create_backup()
        if backup_path:
            print(f"✅ Backup created: {backup_path}")
        
        # Initialize database with latest schema
        print("🔨 Applying schema updates...")
        await init_database()
        
        # Check if we need to migrate data
        async with AsyncSessionLocal() as session:
            # Test if the database has data
            result = await session.execute(select(Activity))
            activities = result.scalars().all()
            
            if not activities:
                print("📥 No existing data found, seeding initial data...")
                await seed_initial_data()
            else:
                print(f"✅ Found {len(activities)} existing activities")
                
                # You can add specific migration logic here
                # For example, add new columns or update data formats
                
                # Example: Update any activities without created_at timestamps
                activities_without_timestamps = [a for a in activities if a.created_at is None]
                if activities_without_timestamps:
                    from datetime import datetime
                    print(f"🔧 Updating {len(activities_without_timestamps)} activities with missing timestamps...")
                    for activity in activities_without_timestamps:
                        activity.created_at = datetime.utcnow()
                    await session.commit()
        
        print("🎉 Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


async def reset_database():
    """Reset database to clean state (DANGER: removes all data)"""
    print("⚠️  WARNING: This will delete ALL data!")
    confirmation = input("Type 'RESET' to confirm: ")
    
    if confirmation != "RESET":
        print("❌ Reset cancelled")
        return False
    
    try:
        # Create backup before reset
        backup_path = await create_backup()
        if backup_path:
            print(f"📦 Backup created: {backup_path}")
        
        # Drop and recreate all tables
        from src.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        # Seed with initial data
        await seed_initial_data()
        
        print("🎉 Database reset completed!")
        return True
        
    except Exception as e:
        print(f"❌ Reset failed: {e}")
        return False


async def check_database_health():
    """Check database health and show statistics"""
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy.orm import selectinload
            
            # Count activities
            result = await session.execute(
                select(Activity).options(selectinload(Activity.participants))
            )
            activities = result.scalars().all()
            
            # Count users
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            # Calculate total enrollments
            total_enrollments = sum(len(activity.participants) for activity in activities)
            
            print("📊 Database Health Report:")
            print(f"   Activities: {len(activities)}")
            print(f"   Users: {len(users)}")
            print(f"   Total Enrollments: {total_enrollments}")
            
            # Show activity details
            print("\n📋 Activity Details:")
            for activity in activities:
                spots_left = activity.max_participants - len(activity.participants)
                status = "FULL" if spots_left == 0 else f"{spots_left} spots left"
                print(f"   • {activity.name}: {len(activity.participants)}/{activity.max_participants} ({status})")
        
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [migrate|reset|health]")
        print("  migrate - Run database migration")
        print("  reset   - Reset database (DANGER: removes all data)")
        print("  health  - Check database health")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "migrate":
        success = asyncio.run(migrate_database())
    elif command == "reset":
        success = asyncio.run(reset_database())
    elif command == "health":
        success = asyncio.run(check_database_health())
    else:
        print(f"Unknown command: {command}")
        success = False
    
    sys.exit(0 if success else 1)

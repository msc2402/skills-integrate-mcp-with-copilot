#!/usr/bin/env python3
"""
Test script to verify the database implementation works correctly.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_database, seed_initial_data, AsyncSessionLocal
from src.models import Activity, User
from sqlalchemy import select


async def test_database():
    """Test database functionality"""
    print("🧪 Testing database implementation...")
    
    try:
        # Initialize database
        await init_database()
        print("✅ Database initialized successfully")
        
        # Seed initial data
        await seed_initial_data()
        print("✅ Initial data seeded successfully")
        
        # Test querying activities
        async with AsyncSessionLocal() as session:
            # Use eager loading to avoid lazy loading issues
            from sqlalchemy.orm import selectinload
            result = await session.execute(
                select(Activity).options(selectinload(Activity.participants))
            )
            activities = result.scalars().all()
            print(f"✅ Found {len(activities)} activities")
            
            for activity in activities[:3]:  # Show first 3
                participants_count = len(activity.participants)
                print(f"   - {activity.name}: {participants_count} participants, {activity.available_spots} spots available")
                
                # Test the new properties
                if activity.is_full:
                    print(f"     ⚠️  Activity is FULL")
                else:
                    print(f"     ✅ Activity has space")
        
        # Test adding a new user and enrolling in activity
        async with AsyncSessionLocal() as session:
            # Create a test user
            test_user = User(email="test@mergington.edu", name="Test Student", grade="10")
            session.add(test_user)
            await session.flush()
            
            # Get an activity with space (use eager loading)
            from sqlalchemy.orm import selectinload
            result = await session.execute(
                select(Activity)
                .options(selectinload(Activity.participants))
                .where(Activity.name == "Chess Club")
            )
            chess_club = result.scalar_one_or_none()
            
            if chess_club and not chess_club.is_full:
                # Enroll the test user
                chess_club.participants.append(test_user)
                await session.commit()
                print("✅ Successfully enrolled test user in Chess Club")
            else:
                print("⚠️  Chess Club is full or not found")
        
        print("🎉 Database implementation test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_database())
    sys.exit(0 if success else 1)

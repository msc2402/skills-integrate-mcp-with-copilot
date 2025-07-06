"""
Database models for the Mergington High School activities system.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Table, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import re

Base = declarative_base()

# Association table for many-to-many relationship between activities and participants
activity_participants = Table(
    'activity_participants',
    Base.metadata,
    Column('activity_id', Integer, ForeignKey('activities.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('enrolled_at', DateTime, default=datetime.utcnow, nullable=False)
)


class User(Base):
    """User model for students and staff"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    grade = Column(String(10), nullable=True)
    student_id = Column(String(50), nullable=True, unique=True)
    role = Column(String(50), default='student', nullable=False)  # student, teacher, admin
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Add constraints
    __table_args__ = (
        CheckConstraint("role IN ('student', 'teacher', 'admin')", name='valid_role'),
        CheckConstraint("email LIKE '%@%'", name='valid_email_format'),
    )
    
    # Relationship to activities through association table
    activities = relationship("Activity", secondary=activity_participants, back_populates="participants")
    
    @validates('email')
    def validate_email(self, key, address):
        """Validate email format"""
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', address):
            raise ValueError('Invalid email format')
        return address.lower()
    
    @validates('role')
    def validate_role(self, key, role):
        """Validate user role"""
        valid_roles = {'student', 'teacher', 'admin'}
        if role not in valid_roles:
            raise ValueError(f'Role must be one of: {valid_roles}')
        return role


class Activity(Base):
    """Activity model for extracurricular activities"""
    __tablename__ = 'activities'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    schedule = Column(String(500), nullable=False)
    max_participants = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Add constraints
    __table_args__ = (
        CheckConstraint('max_participants > 0', name='positive_max_participants'),
        CheckConstraint("length(name) >= 3", name='min_name_length'),
        CheckConstraint("length(description) >= 10", name='min_description_length'),
    )
    
    # Relationship to users through association table
    participants = relationship("User", secondary=activity_participants, back_populates="activities")
    creator = relationship("User", foreign_keys=[created_by])
    
    @validates('max_participants')
    def validate_max_participants(self, key, value):
        """Validate maximum participants is positive"""
        if value <= 0:
            raise ValueError('Maximum participants must be greater than 0')
        return value
    
    @validates('name')
    def validate_name(self, key, name):
        """Validate activity name"""
        if len(name.strip()) < 3:
            raise ValueError('Activity name must be at least 3 characters long')
        return name.strip()
    
    @property
    def available_spots(self):
        """Calculate available spots in the activity"""
        return self.max_participants - len(self.participants)
    
    @property
    def is_full(self):
        """Check if activity is full"""
        return len(self.participants) >= self.max_participants
    participants = relationship("User", secondary=activity_participants, back_populates="activities")
    creator = relationship("User", foreign_keys=[created_by])

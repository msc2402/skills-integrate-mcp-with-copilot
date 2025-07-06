# Mergington High School Activities API

A robust FastAPI application that allows students to view and sign up for extracurricular activities with **persistent database storage**.

## Features

- ✅ **Database Persistence**: All data is stored in a SQLite database and survives server restarts
- ✅ **Robust Data Models**: Proper relationships, constraints, and validation
- ✅ **Error Handling**: Comprehensive error handling with logging
- ✅ **Health Monitoring**: Database health checks and backup functionality
- ✅ **Migration Support**: Database migration and management tools
- ✅ View all available extracurricular activities
- ✅ Sign up for activities with validation (max participants, duplicates)
- ✅ Unregister from activities

## Database Schema

### Users Table
- ID (Primary Key)
- Email (Unique, validated format)
- Name, Grade, Student ID
- Role (student, teacher, admin)
- Created timestamp

### Activities Table
- ID (Primary Key)
- Name (Unique, validated)
- Description (validated minimum length)
- Schedule
- Maximum participants (positive constraint)
- Creator reference
- Created timestamp

### Enrollments (Many-to-Many)
- User ID + Activity ID (Composite Primary Key)
- Enrollment timestamp

## Getting Started

1. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Initialize the database (optional - happens automatically):

   ```bash
   python migrate.py migrate
   ```

3. Run the application:

   ```bash
   python -m uvicorn src.app:app --reload
   ```

4. Open your browser and go to:
   - Web Application: http://localhost:8000
   - API documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Database Management

### Migration Commands

```bash
# Check database health and statistics
python migrate.py health

# Run database migration (safe)
python migrate.py migrate

# Reset database (DANGER: removes all data)
python migrate.py reset
```

### Testing

```bash
# Test database implementation
python test_database.py
```

### Backup

```bash
# Create database backup via API
curl http://localhost:8000/admin/backup
```

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister from an activity                                        |
| GET    | `/health`                                                         | Database health check                                               |
| GET    | `/admin/backup`                                                   | Create database backup                                              |

## Production Deployment

For production deployment:

1. **Database**: Replace SQLite with PostgreSQL
   ```bash
   export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/mergington"
   ```

2. **Environment**: Copy `.env.example` to `.env` and configure
   ```bash
   cp .env.example .env
   # Edit .env with your production settings
   ```

3. **Backup**: Set up automated backups
   ```bash
   # Create backup directory
   mkdir -p ./backups
   ```

## Data Model Features

- **Validation**: Email format, positive participant limits, minimum name lengths
- **Constraints**: Unique emails, valid roles, cascade deletes
- **Relationships**: Proper many-to-many with enrollment timestamps
- **Properties**: Calculated fields like `available_spots` and `is_full`
- **Error Handling**: Graceful handling of database errors with proper HTTP status codes

## Migration from In-Memory Storage

The application has been successfully migrated from in-memory Python dictionaries to a persistent SQLite database with:

- ✅ **Zero Data Loss**: Existing test data preserved during migration
- ✅ **Backward Compatibility**: API endpoints unchanged
- ✅ **Enhanced Features**: Added data validation, constraints, and relationships
- ✅ **Production Ready**: Proper error handling, logging, and health checks
- ✅ **Scalable**: Ready for PostgreSQL migration when needed

## Technical Implementation

- **SQLAlchemy 2.0+** with async support
- **Connection pooling** for better performance
- **Eager loading** to prevent N+1 query problems
- **Transaction management** with proper rollback on errors
- **Logging** for debugging and monitoring
- **Database constraints** for data integrity
- **Migration scripts** for schema updates

# Gryzzly Collaborator Declarations - Architecture Analysis & Implementation Guide

## Project Overview

The Plan Charge V8 application is a full-stack web application that integrates with two external systems:
- **Gryzzly**: Time tracking and project management system
- **PayFit**: HR and payroll system

The application synchronizes data from both systems to provide unified reporting and management capabilities.

## Architecture Summary

### Backend Stack
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **API Structure**: RESTful API with versioning (/api/v1)

### Frontend Stack
- **Framework**: React
- **Routing**: React Router
- **Styling**: CSS modules
- **State Management**: React hooks

### Key Components

#### Database Models (Gryzzly)
1. **GryzzlyUser**: Stores synchronized users from Gryzzly
   - Links to local users via `local_user_id`
   - Contains email, name, and active status
   
2. **GryzzlyProject**: Stores synchronized projects
   - Contains project details, budget info, and client data
   
3. **GryzzlyTimeEntry**: Stores time declarations (the main focus)
   - Links to GryzzlyUser and GryzzlyProject
   - Contains hours, date, description, billable status
   
4. **GryzzlySyncLog**: Tracks synchronization history

## Retrieving Collaborator Declarations

### Current Implementation

The application already has endpoints to retrieve time entries (declarations) for collaborators:

#### API Endpoint
```
GET /api/v1/gryzzly/time-entries
```

#### Query Parameters:
- `skip`: Pagination offset (default: 0)
- `limit`: Number of records (default: 100)
- `start_date`: Filter by start date
- `end_date`: Filter by end date
- `user_id`: Filter by specific user ID
- `project_id`: Filter by specific project ID
- `is_billable`: Filter billable entries
- `is_validated`: Filter validated entries

### Data Flow for Retrieving Declarations

1. **Synchronization Process**:
   - Gryzzly data is synchronized via background tasks
   - The `GryzzlySyncService` fetches data from Gryzzly API
   - Data is stored in local PostgreSQL database

2. **Retrieval Process**:
   - Frontend makes API call to `/api/v1/gryzzly/time-entries`
   - Backend queries `gryzzly_time_entries` table with filters
   - Returns paginated results with user and project information

### Implementation Steps to Enhance Declaration Retrieval

#### 1. Add Endpoint for Declarations by Collaborator
```python
@router.get("/users/{user_id}/declarations", response_model=List[GryzzlyTimeEntryInDB])
def get_user_declarations(
    user_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get all declarations for a specific collaborator"""
    # Implementation here
```

#### 2. Add Aggregation Endpoint
```python
@router.get("/declarations/summary", response_model=DeclarationsSummary)
def get_declarations_summary(
    start_date: datetime,
    end_date: datetime,
    group_by: str = Query("user", enum=["user", "project", "day", "week", "month"]),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get aggregated declarations summary"""
    # Implementation here
```

#### 3. Enhance Frontend Components

Create new components in `frontend/src/components/gryzzly/`:
- `CollaboratorDeclarations.js`: Display declarations for a specific user
- `DeclarationsSummary.js`: Show aggregated data with charts

### Database Queries for Common Use Cases

#### Get All Declarations for a Collaborator
```sql
SELECT 
    te.*,
    u.first_name,
    u.last_name,
    u.email,
    p.name as project_name
FROM gryzzly_time_entries te
JOIN gryzzly_users u ON te.gryzzly_user_id = u.id
JOIN gryzzly_projects p ON te.gryzzly_project_id = p.id
WHERE u.gryzzly_id = 'USER_ID'
AND te.entry_date BETWEEN '2025-01-01' AND '2025-01-31'
ORDER BY te.entry_date DESC;
```

#### Get Total Hours by Collaborator
```sql
SELECT 
    u.gryzzly_id,
    u.first_name,
    u.last_name,
    SUM(te.hours) as total_hours,
    COUNT(DISTINCT te.entry_date) as days_worked
FROM gryzzly_time_entries te
JOIN gryzzly_users u ON te.gryzzly_user_id = u.id
WHERE te.entry_date BETWEEN '2025-01-01' AND '2025-01-31'
GROUP BY u.gryzzly_id, u.first_name, u.last_name
ORDER BY total_hours DESC;
```

### API Integration with Gryzzly

The `GryzzlyApiClient` class handles communication with Gryzzly API:

```python
# Get time entries for a specific user
async def get_user_time_entries(user_id: str, start_date: datetime, end_date: datetime):
    async with GryzzlyApiClient() as client:
        entries = await client.get_time_entries(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
    return entries
```

### Security Considerations

1. **Authentication**: All endpoints require authenticated users
2. **Authorization**: Consider adding role-based access control
3. **Data Privacy**: Sensitive data should be encrypted or masked
4. **Rate Limiting**: API calls to Gryzzly are rate-limited (50 requests/10 seconds)

### Next Steps

1. **Implement Enhanced Endpoints**: Add the suggested endpoints for better declaration retrieval
2. **Create Dashboard Views**: Build frontend components for declaration visualization
3. **Add Export Functionality**: Allow exporting declarations to CSV/Excel
4. **Implement Caching**: Cache frequently accessed data to improve performance
5. **Add Real-time Updates**: Consider WebSocket for live updates during sync

### Testing

The project includes test infrastructure:
- API tests in `scripts/comprehensive-test-suite.sh`
- Mock Gryzzly client for testing without API access
- Database seeders for test data

### Configuration

Key environment variables for Gryzzly integration:
- `GRYZZLY_API_URL`: Base URL for Gryzzly API
- `GRYZZLY_API_KEY`: Authentication key
- `GRYZZLY_USE_MOCK`: Use mock client for testing
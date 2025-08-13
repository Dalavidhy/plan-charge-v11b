# Frontend-Backend Integration Guide

## Overview

This document provides a comprehensive guide for the integration between the Plan Charge v11b frontend (React + TypeScript) and backend (FastAPI + PostgreSQL).

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   React App     │────▶│   FastAPI       │────▶│   PostgreSQL    │
│   (Port 3000)   │     │   (Port 8000)   │     │   (Port 5432)   │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                        │                        │
        │                        │                        │
        ▼                        ▼                        ▼
   ┌─────────┐            ┌─────────┐            ┌─────────┐
   │  Nginx  │            │  Redis  │            │ Celery  │
   │ (Proxy) │            │ (Cache) │            │ (Queue) │
   └─────────┘            └─────────┘            └─────────┘
```

## Authentication Flow

### 1. Login Process

```typescript
// Frontend: Login request
const response = await authApi.login(email, password);
// Stores tokens in localStorage
localStorage.setItem('accessToken', response.access_token);
localStorage.setItem('refreshToken', response.refresh_token);
```

```python
# Backend: Login endpoint
@router.post("/auth/login")
async def login(credentials: LoginRequest) -> LoginResponse:
    # Validate credentials
    # Generate JWT tokens
    # Return tokens and user info
```

### 2. Token Refresh

```typescript
// Frontend: Automatic token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const newToken = await refreshToken();
      // Retry original request with new token
    }
  }
);
```

### 3. Protected Routes

```typescript
// Frontend: Protected route wrapper
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" />;
  return children;
}
```

## API Integration Patterns

### 1. Data Fetching with React Query

```typescript
// Frontend: Fetching data
const { data, isLoading, error } = useQuery({
  queryKey: ['projects', filters],
  queryFn: () => projectsApi.list(filters),
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

### 2. Mutations

```typescript
// Frontend: Creating/updating data
const mutation = useMutation({
  mutationFn: (data) => projectsApi.create(data),
  onSuccess: () => {
    queryClient.invalidateQueries(['projects']);
    toast.success('Project created');
  },
  onError: (error) => {
    toast.error(error.message);
  },
});
```

### 3. Real-time Updates (WebSocket)

```typescript
// Frontend: WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Update UI based on real-time data
};
```

## Feature Implementation Examples

### 1. Organization Management

#### Backend Endpoints:
- `GET /api/v1/orgs` - List organizations
- `POST /api/v1/orgs` - Create organization
- `GET /api/v1/orgs/:id` - Get organization details
- `PATCH /api/v1/orgs/:id` - Update organization
- `DELETE /api/v1/orgs/:id` - Delete organization

#### Frontend Components:
- `OrganizationList` - Display organizations
- `OrganizationForm` - Create/edit form
- `OrganizationDetail` - View details

#### State Management:
```typescript
// Zustand store for organization state
const useOrganizationStore = create((set) => ({
  organizations: [],
  selectedOrg: null,
  setOrganizations: (orgs) => set({ organizations: orgs }),
  setSelectedOrg: (org) => set({ selectedOrg: org }),
}));
```

### 2. Resource Allocation

#### Conflict Detection:
```python
# Backend: Detect allocation conflicts
def detect_conflicts(allocation: Allocation) -> List[Conflict]:
    overlapping = db.query(Allocation).filter(
        Allocation.person_id == allocation.person_id,
        Allocation.start_date <= allocation.end_date,
        Allocation.end_date >= allocation.start_date
    ).all()
    
    conflicts = []
    for overlap in overlapping:
        total_allocation = calculate_total_allocation(overlap, allocation)
        if total_allocation > 100:
            conflicts.append(create_conflict(overlap, allocation))
    return conflicts
```

#### Frontend Visualization:
```typescript
// Allocation grid component
<AllocationGrid
  person={person}
  week={currentWeek}
  allocations={allocations}
  onAllocationChange={handleAllocationChange}
  onConflict={showConflictModal}
/>
```

### 3. Reporting & Analytics

#### Data Aggregation:
```python
# Backend: Utilization report
@router.get("/reports/utilization")
async def get_utilization_report(
    group_by: str = "team",
    from_date: date = None,
    to_date: date = None
) -> UtilizationReport:
    # Aggregate allocation data
    # Calculate utilization percentages
    # Return structured report data
```

#### Chart Visualization:
```typescript
// Frontend: Utilization chart
<UtilizationChart
  data={utilizationData}
  groupBy="team"
  dateRange={{ from, to }}
  onDrillDown={handleDrillDown}
/>
```

## Testing Strategy

### 1. Unit Tests

#### Backend:
```python
# Test authentication
def test_login_with_valid_credentials():
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

#### Frontend:
```typescript
// Test login component
test('should display error on invalid credentials', async () => {
  render(<LoginPage />);
  fireEvent.click(screen.getByText('Sign in'));
  await waitFor(() => {
    expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
  });
});
```

### 2. Integration Tests

```typescript
// Test complete user flow
test('user can create and allocate resources', async () => {
  // Login
  await loginAs('manager@example.com');
  
  // Create project
  await createProject({ name: 'Test Project' });
  
  // Allocate resource
  await allocateResource({
    person: 'John Doe',
    project: 'Test Project',
    allocation: 50
  });
  
  // Verify allocation
  expect(await getAllocations()).toContainEqual(
    expect.objectContaining({ allocation: 50 })
  );
});
```

### 3. E2E Tests

```typescript
// Playwright E2E test
test('complete resource planning workflow', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.fill('[name=email]', 'admin@example.com');
  await page.fill('[name=password]', 'password123');
  await page.click('button[type=submit]');
  
  // Navigate to allocations
  await page.click('text=Allocations');
  
  // Create new allocation
  await page.click('text=New Allocation');
  await page.selectOption('[name=person]', 'John Doe');
  await page.selectOption('[name=project]', 'Project Alpha');
  await page.fill('[name=percentage]', '75');
  await page.click('text=Save');
  
  // Verify conflict detection
  await expect(page.locator('.conflict-warning')).toBeVisible();
});
```

## Performance Optimization

### 1. Backend Optimizations

```python
# Use database indexes
class Allocation(Base):
    __table_args__ = (
        Index('idx_person_dates', 'person_id', 'start_date', 'end_date'),
        Index('idx_project_dates', 'project_id', 'start_date', 'end_date'),
    )

# Implement caching
@cache(expire=300)  # 5 minutes
async def get_utilization_data(team_id: str):
    # Expensive calculation cached
    return calculate_utilization(team_id)
```

### 2. Frontend Optimizations

```typescript
// Virtual scrolling for large lists
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={people.length}
  itemSize={50}
  width="100%"
>
  {({ index, style }) => (
    <PersonRow person={people[index]} style={style} />
  )}
</FixedSizeList>

// Code splitting
const ReportsPage = lazy(() => import('./pages/reports'));

// Memoization
const ExpensiveComponent = memo(({ data }) => {
  // Component only re-renders when data changes
});
```

## Deployment

### 1. Development

```bash
# Start all services
docker-compose up -d

# Access points
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
```

### 2. Production

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Environment variables
DATABASE_URL=postgresql://user:pass@db:5432/plancharge
REDIS_URL=redis://redis:6379
JWT_SECRET_KEY=<secure-random-key>
CORS_ORIGINS=https://plancharge.example.com
```

## Security Considerations

### 1. Authentication
- JWT tokens with short expiry (15 min access, 30 days refresh)
- Secure token storage (httpOnly cookies in production)
- Password hashing with bcrypt

### 2. Authorization
- Role-based access control (RBAC)
- Resource-level permissions
- API rate limiting

### 3. Data Protection
- Input validation and sanitization
- SQL injection prevention (ORM parameterized queries)
- XSS protection (React automatic escaping)
- CSRF protection (SameSite cookies)

## Monitoring & Logging

### 1. Application Monitoring

```python
# Backend logging
logger.info(f"User {user_id} allocated {percent}% to project {project_id}")

# Structured logging
logger.info("allocation_created", extra={
    "user_id": user_id,
    "project_id": project_id,
    "allocation": percent,
    "timestamp": datetime.utcnow()
})
```

### 2. Error Tracking

```typescript
// Frontend error boundary
class ErrorBoundary extends Component {
  componentDidCatch(error, errorInfo) {
    // Send to error tracking service
    Sentry.captureException(error, { contexts: { react: errorInfo } });
  }
}
```

### 3. Performance Monitoring

```typescript
// Track API response times
api.interceptors.response.use((response) => {
  const duration = Date.now() - response.config.metadata.startTime;
  analytics.track('api_request', {
    endpoint: response.config.url,
    duration,
    status: response.status
  });
  return response;
});
```

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure backend CORS_ORIGINS includes frontend URL
   - Check proxy configuration in development

2. **Authentication Failures**
   - Verify JWT_SECRET_KEY is consistent
   - Check token expiry times
   - Ensure refresh token rotation is working

3. **Database Connection Issues**
   - Verify DATABASE_URL is correct
   - Check network connectivity between containers
   - Ensure migrations are applied

4. **Performance Issues**
   - Enable database query logging to identify slow queries
   - Use React DevTools Profiler to identify rendering bottlenecks
   - Check network tab for unnecessary API calls

## API Documentation

The complete API documentation is available at:
- Development: http://localhost:8000/docs
- Production: https://api.plancharge.example.com/docs

## Support

For issues or questions:
- Create an issue in the repository
- Contact the development team
- Check the troubleshooting guide above
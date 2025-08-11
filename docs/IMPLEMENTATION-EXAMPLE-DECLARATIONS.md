# Implementation Example: Retrieving Collaborator Declarations

## Backend Implementation

### 1. Enhanced API Endpoint (Add to `backend/app/api/v1/endpoints/gryzzly.py`)

```python
@router.get("/collaborators/{collaborator_id}/declarations", response_model=CollaboratorDeclarationsResponse)
async def get_collaborator_declarations(
    collaborator_id: str,
    start_date: datetime = Query(..., description="Start date for declarations"),
    end_date: datetime = Query(..., description="End date for declarations"),
    include_details: bool = Query(True, description="Include project and task details"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> CollaboratorDeclarationsResponse:
    """
    Get all time declarations for a specific collaborator within a date range.
    Returns declarations with project details and aggregated statistics.
    """
    
    # Find the Gryzzly user
    gryzzly_user = db.query(GryzzlyUser).filter(
        GryzzlyUser.gryzzly_id == collaborator_id
    ).first()
    
    if not gryzzly_user:
        raise HTTPException(
            status_code=404,
            detail=f"Collaborator with ID {collaborator_id} not found"
        )
    
    # Query time entries with joins for details
    query = db.query(GryzzlyTimeEntry).filter(
        GryzzlyTimeEntry.gryzzly_user_id == gryzzly_user.id,
        GryzzlyTimeEntry.entry_date >= start_date,
        GryzzlyTimeEntry.entry_date <= end_date
    )
    
    if include_details:
        query = query.options(
            selectinload(GryzzlyTimeEntry.gryzzly_project),
            selectinload(GryzzlyTimeEntry.gryzzly_user)
        )
    
    declarations = query.order_by(GryzzlyTimeEntry.entry_date.desc()).all()
    
    # Calculate statistics
    total_hours = sum(d.hours for d in declarations)
    billable_hours = sum(d.hours for d in declarations if d.is_billable)
    days_worked = len(set(d.entry_date.date() for d in declarations))
    
    # Group by project
    project_hours = {}
    for declaration in declarations:
        project_name = declaration.gryzzly_project.name if declaration.gryzzly_project else "Unknown"
        if project_name not in project_hours:
            project_hours[project_name] = {
                "total_hours": 0,
                "billable_hours": 0,
                "entries_count": 0
            }
        project_hours[project_name]["total_hours"] += declaration.hours
        if declaration.is_billable:
            project_hours[project_name]["billable_hours"] += declaration.hours
        project_hours[project_name]["entries_count"] += 1
    
    return CollaboratorDeclarationsResponse(
        collaborator=gryzzly_user,
        declarations=declarations,
        statistics={
            "total_hours": total_hours,
            "billable_hours": billable_hours,
            "non_billable_hours": total_hours - billable_hours,
            "days_worked": days_worked,
            "average_hours_per_day": total_hours / days_worked if days_worked > 0 else 0,
            "project_breakdown": project_hours
        },
        period={
            "start_date": start_date,
            "end_date": end_date
        }
    )


@router.get("/declarations/weekly-summary", response_model=List[WeeklySummary])
async def get_weekly_declarations_summary(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    collaborator_ids: Optional[List[str]] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> List[WeeklySummary]:
    """
    Get weekly summary of declarations for multiple collaborators.
    Useful for management dashboards and reporting.
    """
    
    query = db.query(
        GryzzlyTimeEntry.gryzzly_user_id,
        func.date_trunc('week', GryzzlyTimeEntry.entry_date).label('week'),
        func.sum(GryzzlyTimeEntry.hours).label('total_hours'),
        func.sum(
            case(
                (GryzzlyTimeEntry.is_billable == True, GryzzlyTimeEntry.hours),
                else_=0
            )
        ).label('billable_hours'),
        func.count(distinct(GryzzlyTimeEntry.entry_date)).label('days_worked')
    ).filter(
        GryzzlyTimeEntry.entry_date >= start_date,
        GryzzlyTimeEntry.entry_date <= end_date
    )
    
    if collaborator_ids:
        user_ids = db.query(GryzzlyUser.id).filter(
            GryzzlyUser.gryzzly_id.in_(collaborator_ids)
        ).subquery()
        query = query.filter(GryzzlyTimeEntry.gryzzly_user_id.in_(user_ids))
    
    weekly_data = query.group_by(
        GryzzlyTimeEntry.gryzzly_user_id,
        'week'
    ).all()
    
    # Format results
    results = []
    for row in weekly_data:
        user = db.query(GryzzlyUser).get(row.gryzzly_user_id)
        results.append(WeeklySummary(
            user_id=user.gryzzly_id,
            user_name=f"{user.first_name} {user.last_name}",
            week_start=row.week,
            total_hours=row.total_hours,
            billable_hours=row.billable_hours,
            days_worked=row.days_worked
        ))
    
    return results
```

### 2. Add Response Schemas (Add to `backend/app/schemas/gryzzly.py`)

```python
class DeclarationStatistics(BaseModel):
    total_hours: float
    billable_hours: float
    non_billable_hours: float
    days_worked: int
    average_hours_per_day: float
    project_breakdown: Dict[str, Dict[str, float]]

class CollaboratorDeclarationsResponse(BaseModel):
    collaborator: GryzzlyUserInDB
    declarations: List[GryzzlyTimeEntryInDB]
    statistics: DeclarationStatistics
    period: Dict[str, datetime]

class WeeklySummary(BaseModel):
    user_id: str
    user_name: str
    week_start: datetime
    total_hours: float
    billable_hours: float
    days_worked: int
```

## Frontend Implementation

### 1. Service Layer (Create `frontend/src/services/declarations.service.js`)

```javascript
import api from './api';

const declarationsService = {
  // Get declarations for a specific collaborator
  async getCollaboratorDeclarations(collaboratorId, startDate, endDate, includeDetails = true) {
    try {
      const response = await api.get(
        `/gryzzly/collaborators/${collaboratorId}/declarations`,
        {
          params: {
            start_date: startDate,
            end_date: endDate,
            include_details: includeDetails
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching collaborator declarations:', error);
      throw error;
    }
  },

  // Get weekly summary for multiple collaborators
  async getWeeklySummary(startDate, endDate, collaboratorIds = null) {
    try {
      const params = {
        start_date: startDate,
        end_date: endDate
      };
      
      if (collaboratorIds && collaboratorIds.length > 0) {
        params.collaborator_ids = collaboratorIds;
      }

      const response = await api.get('/gryzzly/declarations/weekly-summary', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching weekly summary:', error);
      throw error;
    }
  },

  // Export declarations to CSV
  async exportDeclarations(collaboratorId, startDate, endDate) {
    try {
      const data = await this.getCollaboratorDeclarations(
        collaboratorId,
        startDate,
        endDate
      );
      
      // Convert to CSV
      const csv = this.convertToCSV(data.declarations);
      
      // Download file
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `declarations_${collaboratorId}_${startDate}_${endDate}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting declarations:', error);
      throw error;
    }
  },

  convertToCSV(declarations) {
    const headers = [
      'Date',
      'Project',
      'Task',
      'Hours',
      'Description',
      'Billable',
      'Validated'
    ];
    
    const rows = declarations.map(d => [
      new Date(d.entry_date).toLocaleDateString(),
      d.gryzzly_project?.name || '',
      d.task_name || '',
      d.hours,
      d.description || '',
      d.is_billable ? 'Yes' : 'No',
      d.is_validated ? 'Yes' : 'No'
    ]);
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');
    
    return csvContent;
  }
};

export default declarationsService;
```

### 2. React Component (Create `frontend/src/components/gryzzly/CollaboratorDeclarations.js`)

```javascript
import React, { useState, useEffect } from 'react';
import declarationsService from '../../services/declarations.service';
import './CollaboratorDeclarations.css';

const CollaboratorDeclarations = ({ collaboratorId }) => {
  const [declarations, setDeclarations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState({
    startDate: new Date(new Date().setMonth(new Date().getMonth() - 1)).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    fetchDeclarations();
  }, [collaboratorId, dateRange]);

  const fetchDeclarations = async () => {
    try {
      setLoading(true);
      const data = await declarationsService.getCollaboratorDeclarations(
        collaboratorId,
        dateRange.startDate,
        dateRange.endDate
      );
      setDeclarations(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch declarations');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      await declarationsService.exportDeclarations(
        collaboratorId,
        dateRange.startDate,
        dateRange.endDate
      );
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  if (loading) return <div className="loading">Loading declarations...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!declarations) return null;

  const { collaborator, statistics, declarations: timeEntries } = declarations;

  return (
    <div className="collaborator-declarations">
      <div className="header">
        <h2>Declarations for {collaborator.first_name} {collaborator.last_name}</h2>
        <div className="date-filters">
          <input
            type="date"
            value={dateRange.startDate}
            onChange={(e) => setDateRange({ ...dateRange, startDate: e.target.value })}
          />
          <span>to</span>
          <input
            type="date"
            value={dateRange.endDate}
            onChange={(e) => setDateRange({ ...dateRange, endDate: e.target.value })}
          />
          <button onClick={fetchDeclarations}>Update</button>
          <button onClick={handleExport}>Export CSV</button>
        </div>
      </div>

      <div className="statistics">
        <div className="stat-card">
          <h3>Total Hours</h3>
          <p className="stat-value">{statistics.total_hours.toFixed(2)}</p>
        </div>
        <div className="stat-card">
          <h3>Billable Hours</h3>
          <p className="stat-value">{statistics.billable_hours.toFixed(2)}</p>
        </div>
        <div className="stat-card">
          <h3>Days Worked</h3>
          <p className="stat-value">{statistics.days_worked}</p>
        </div>
        <div className="stat-card">
          <h3>Avg Hours/Day</h3>
          <p className="stat-value">{statistics.average_hours_per_day.toFixed(2)}</p>
        </div>
      </div>

      <div className="project-breakdown">
        <h3>Hours by Project</h3>
        <table>
          <thead>
            <tr>
              <th>Project</th>
              <th>Total Hours</th>
              <th>Billable Hours</th>
              <th>Entries</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(statistics.project_breakdown).map(([project, data]) => (
              <tr key={project}>
                <td>{project}</td>
                <td>{data.total_hours.toFixed(2)}</td>
                <td>{data.billable_hours.toFixed(2)}</td>
                <td>{data.entries_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="declarations-list">
        <h3>Time Entries</h3>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Project</th>
              <th>Task</th>
              <th>Hours</th>
              <th>Description</th>
              <th>Billable</th>
              <th>Validated</th>
            </tr>
          </thead>
          <tbody>
            {timeEntries.map((entry) => (
              <tr key={entry.id}>
                <td>{new Date(entry.entry_date).toLocaleDateString()}</td>
                <td>{entry.gryzzly_project?.name || 'N/A'}</td>
                <td>{entry.task_name || 'N/A'}</td>
                <td>{entry.hours}</td>
                <td>{entry.description || '-'}</td>
                <td>{entry.is_billable ? '✓' : '✗'}</td>
                <td>{entry.is_validated ? '✓' : '✗'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CollaboratorDeclarations;
```

### 3. Dashboard Component (Create `frontend/src/components/gryzzly/DeclarationsDashboard.js`)

```javascript
import React, { useState, useEffect } from 'react';
import declarationsService from '../../services/declarations.service';
import CollaboratorDeclarations from './CollaboratorDeclarations';
import './DeclarationsDashboard.css';

const DeclarationsDashboard = () => {
  const [selectedCollaborator, setSelectedCollaborator] = useState(null);
  const [collaborators, setCollaborators] = useState([]);
  const [weeklySummary, setWeeklySummary] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCollaborators();
    fetchWeeklySummary();
  }, []);

  const fetchCollaborators = async () => {
    try {
      const response = await api.get('/gryzzly/users');
      setCollaborators(response.data);
    } catch (error) {
      console.error('Failed to fetch collaborators:', error);
    }
  };

  const fetchWeeklySummary = async () => {
    try {
      const endDate = new Date();
      const startDate = new Date();
      startDate.setMonth(startDate.getMonth() - 3); // Last 3 months

      const summary = await declarationsService.getWeeklySummary(
        startDate.toISOString(),
        endDate.toISOString()
      );
      setWeeklySummary(summary);
    } catch (error) {
      console.error('Failed to fetch weekly summary:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading dashboard...</div>;

  return (
    <div className="declarations-dashboard">
      <h1>Time Declarations Dashboard</h1>
      
      <div className="collaborator-selector">
        <h2>Select Collaborator</h2>
        <select 
          value={selectedCollaborator || ''} 
          onChange={(e) => setSelectedCollaborator(e.target.value)}
        >
          <option value="">Choose a collaborator...</option>
          {collaborators.map(collab => (
            <option key={collab.gryzzly_id} value={collab.gryzzly_id}>
              {collab.first_name} {collab.last_name} - {collab.email}
            </option>
          ))}
        </select>
      </div>

      {selectedCollaborator && (
        <CollaboratorDeclarations collaboratorId={selectedCollaborator} />
      )}

      <div className="weekly-summary">
        <h2>Weekly Summary (All Collaborators)</h2>
        <table>
          <thead>
            <tr>
              <th>Week Starting</th>
              <th>Collaborator</th>
              <th>Total Hours</th>
              <th>Billable Hours</th>
              <th>Days Worked</th>
            </tr>
          </thead>
          <tbody>
            {weeklySummary.map((week, index) => (
              <tr key={index}>
                <td>{new Date(week.week_start).toLocaleDateString()}</td>
                <td>{week.user_name}</td>
                <td>{week.total_hours.toFixed(2)}</td>
                <td>{week.billable_hours.toFixed(2)}</td>
                <td>{week.days_worked}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DeclarationsDashboard;
```

## Usage Instructions

1. **Add the new endpoints** to your backend API
2. **Create the service layer** in your frontend
3. **Add the React components** to your application
4. **Import and use** the DeclarationsDashboard component in your main app

The implementation provides:
- Individual collaborator declaration views
- Statistics and project breakdowns
- Weekly summaries for management
- CSV export functionality
- Date range filtering
- Real-time updates when changing filters

This solution integrates seamlessly with your existing Gryzzly synchronization infrastructure and provides a comprehensive view of collaborator time declarations.
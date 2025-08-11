# 🎫 Restaurant Ticket Feature - Detailed Implementation Workflow

## 📋 Feature Overview
**Feature**: Restaurant Ticket (Ticket Restaurant) Management System  
**Purpose**: Generate monthly CSV reports for restaurant ticket allocation based on working days and absences  
**Complexity**: Medium-High  
**Estimated Duration**: 2-3 weeks  

## 🎯 Requirements Summary
1. Map employee matricule numbers between database and TR system
2. Calculate working days minus absence days using PayFit API
3. Generate CSV file in format: `tickets_restau_<YYYY-MM>.csv`
4. Create dedicated UI page with preview and download functionality
5. Implement comprehensive testing (unit + integration)

## ⚠️ Technical Risks & Mitigation

### 🔴 High Priority Risks
1. **PayFit API Limitations**
   - **Risk**: API rate limits or downtime affecting calculations
   - **Mitigation**: Implement caching layer, retry logic, and fallback to last known data
   
2. **Data Mapping Failures**
   - **Risk**: Missing or inconsistent matricule numbers between systems
   - **Mitigation**: Validation checks, manual override capability, audit logs

3. **Working Days Calculation Accuracy**
   - **Risk**: Incorrect calculation due to holidays, partial days, or edge cases
   - **Mitigation**: Comprehensive holiday calendar, configurable rules engine

### 🟡 Medium Priority Risks
4. **CSV Format Compatibility**
   - **Risk**: TR system rejects CSV due to format issues
   - **Mitigation**: Strict validation against template, format versioning

5. **Performance with Large Datasets**
   - **Risk**: Timeout or memory issues for companies with many employees
   - **Mitigation**: Pagination, background processing, progress indicators

## 🔗 Dependencies Analysis

### Internal Dependencies
- **PayFit Integration Module** ✅ (Exists)
- **User Management System** ✅ (Exists)
- **Authentication & Authorization** ✅ (Exists)
- **File Generation Service** ⚠️ (Needs enhancement)

### External Dependencies
- **PayFit API** (Absences endpoint)
- **Restaurant Ticket System** (CSV format specification)
- **Holiday Calendar Service** (For working days calculation)

### New Components Required
1. Matricule mapping service
2. Working days calculator
3. CSV generator for TR format
4. File download service
5. Restaurant ticket management UI

## 📊 Data Model Changes

### New Tables Required
```sql
-- Restaurant Ticket Configurations
CREATE TABLE restaurant_ticket_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    default_monthly_tickets INTEGER DEFAULT 20,
    ticket_value DECIMAL(10,2) DEFAULT 11.00,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Employee Matricule Mapping
CREATE TABLE employee_matricule_mapping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    payfit_employee_id UUID REFERENCES payfit_employees(id),
    matricule_tr VARCHAR(50) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Restaurant Ticket Generation Logs
CREATE TABLE restaurant_ticket_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    generated_by UUID REFERENCES users(id),
    file_path VARCHAR(255),
    employee_count INTEGER,
    total_tickets INTEGER,
    status VARCHAR(50), -- draft, generated, sent
    generated_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);
```

### Migration Requirements
- Add `matricule` column to `payfit_employees` table ✅ (Already exists)
- Create indexes for performance optimization
- Add audit trail for compliance

## 🛠️ Implementation Phases

### Phase 1: Foundation & Data Layer (Week 1, Days 1-3)

#### Task 1.1: Database Schema Implementation
**Persona**: Backend Developer  
**Estimated Time**: 4 hours  
**Dependencies**: None  
**MCP Context**: SQLAlchemy patterns, PostgreSQL best practices

**Implementation Steps**:
1. **Create Alembic migration** (1 hour)
   ```python
   # alembic/versions/009_add_restaurant_ticket_tables.py
   ```
   - Define restaurant_ticket_configs table
   - Create employee_matricule_mapping table
   - Add restaurant_ticket_logs table
   
2. **Implement SQLAlchemy models** (1 hour)
   ```python
   # app/models/restaurant_ticket.py
   ```
   - RestaurantTicketConfig model
   - EmployeeMatriculeMapping model
   - RestaurantTicketLog model
   
3. **Add relationships and constraints** (1 hour)
   - Foreign key relationships
   - Unique constraints on matricule
   - Composite indexes for queries
   
4. **Migration testing** (1 hour)
   - Test upgrade/downgrade
   - Verify constraints
   - Performance testing

**Acceptance Criteria**:
- [ ] Migration runs without errors
- [ ] All constraints are enforced
- [ ] Indexes improve query performance
- [ ] Rollback works correctly

#### Task 1.2: Matricule Mapping Service
**Persona**: Backend Developer  
**Estimated Time**: 6 hours  
**Dependencies**: Task 1.1  
**MCP Context**: Service layer patterns, data validation

**Implementation Steps**:
1. **Create mapping service** (2 hours)
   ```python
   # app/services/matricule_mapping.py
   class MatriculeMapingService:
       def create_mapping(user_id, matricule_tr)
       def update_mapping(mapping_id, matricule_tr)
       def get_mapping_by_user(user_id)
       def validate_matricule_format(matricule)
       def bulk_import_mappings(csv_data)
   ```

2. **Implement validation logic** (2 hours)
   - Matricule format validation
   - Duplicate checking
   - Cross-system verification
   
3. **Create bulk import functionality** (1 hour)
   - CSV parser for initial import
   - Error handling and reporting
   - Transaction management
   
4. **Add audit logging** (1 hour)
   - Track all mapping changes
   - User action logging
   - Compliance reporting

**Acceptance Criteria**:
- [ ] Matricule validation prevents invalid formats
- [ ] No duplicate matricules allowed
- [ ] Bulk import handles errors gracefully
- [ ] All changes are audited

### Phase 2: Core Business Logic (Week 1, Days 4-5)

#### Task 2.1: Working Days Calculator
**Persona**: Backend Developer  
**Estimated Time**: 8 hours  
**Dependencies**: PayFit integration  
**MCP Context**: Business logic patterns, date calculations

**Implementation Steps**:
1. **Create calculator service** (3 hours)
   ```python
   # app/services/working_days_calculator.py
   class WorkingDaysCalculator:
       def calculate_working_days(year, month)
       def get_holidays(year, month)
       def subtract_absences(working_days, absences)
       def handle_partial_days(absence)
   ```

2. **Implement holiday calendar** (2 hours)
   - French public holidays
   - Company-specific holidays
   - Regional variations
   - Configurable holiday rules

3. **PayFit absence integration** (2 hours)
   - Fetch absences for period
   - Handle different absence types
   - Calculate partial day absences
   - Cache absence data

4. **Edge case handling** (1 hour)
   - Month boundaries
   - Partial month employment
   - Overlapping absences
   - Invalid data handling

**Acceptance Criteria**:
- [ ] Correctly calculates working days for any month
- [ ] Handles all French public holidays
- [ ] Accurately processes PayFit absences
- [ ] Edge cases return sensible results

#### Task 2.2: CSV Generator Service
**Persona**: Backend Developer  
**Estimated Time**: 6 hours  
**Dependencies**: Task 2.1  
**MCP Context**: File generation patterns, CSV standards

**Implementation Steps**:
1. **Create generator service** (2 hours)
   ```python
   # app/services/restaurant_ticket_generator.py
   class RestaurantTicketGenerator:
       def generate_monthly_report(year, month)
       def format_csv_row(employee_data)
       def validate_csv_format(csv_content)
       def save_to_file(csv_content, filepath)
   ```

2. **Implement CSV formatting** (2 hours)
   - Follow template structure
   - Handle special characters
   - Ensure encoding compatibility
   - Add data validation

3. **File management** (1 hour)
   - Secure file storage
   - Unique filename generation
   - Cleanup old files
   - Access control

4. **Error handling** (1 hour)
   - Missing data handling
   - Format validation
   - Generation failure recovery
   - User notification

**Acceptance Criteria**:
- [ ] CSV matches exact template format
- [ ] Special characters handled correctly
- [ ] Files stored securely
- [ ] Errors reported clearly

### Phase 3: API Development (Week 2, Days 1-2)

#### Task 3.1: Restaurant Ticket API Endpoints
**Persona**: Backend Developer  
**Estimated Time**: 8 hours  
**Dependencies**: Phase 2 completed  
**MCP Context**: FastAPI patterns, REST standards

**Implementation Steps**:
1. **Create API router** (2 hours)
   ```python
   # app/api/v1/endpoints/restaurant_tickets.py
   router = APIRouter(prefix="/restaurant-tickets")
   
   @router.post("/generate")
   @router.get("/preview/{year}/{month}")
   @router.get("/download/{log_id}")
   @router.get("/history")
   @router.post("/matricule-mapping")
   ```

2. **Implement generation endpoint** (2 hours)
   - Parameter validation
   - Authorization checks
   - Async processing
   - Progress tracking

3. **Preview functionality** (2 hours)
   - Return JSON preview
   - Pagination support
   - Filtering options
   - Summary statistics

4. **Download endpoint** (2 hours)
   - Secure file serving
   - Access control
   - Download logging
   - File cleanup

**Acceptance Criteria**:
- [ ] All endpoints follow REST standards
- [ ] Proper authorization enforced
- [ ] File downloads are secure
- [ ] API documentation complete

#### Task 3.2: API Integration & Testing
**Persona**: Backend Developer  
**Estimated Time**: 6 hours  
**Dependencies**: Task 3.1  
**MCP Context**: API testing patterns, integration testing

**Implementation Steps**:
1. **Create API schemas** (2 hours)
   ```python
   # app/schemas/restaurant_ticket.py
   class RestaurantTicketGenerate(BaseModel)
   class RestaurantTicketPreview(BaseModel)
   class MatriculeMappingCreate(BaseModel)
   ```

2. **Integration with services** (2 hours)
   - Wire up services to endpoints
   - Handle async operations
   - Add caching layer
   - Error propagation

3. **API tests** (2 hours)
   - Unit tests for each endpoint
   - Integration tests
   - Authorization tests
   - Error scenario tests

**Acceptance Criteria**:
- [ ] All endpoints have schemas
- [ ] Services properly integrated
- [ ] Tests cover happy path and errors
- [ ] Performance meets requirements

### Phase 4: Frontend Implementation (Week 2, Days 3-5)

#### Task 4.1: Restaurant Ticket UI Components
**Persona**: Frontend Developer  
**Estimated Time**: 10 hours  
**Dependencies**: API endpoints ready  
**MCP Context**: React patterns, Material-UI components

**Implementation Steps**:
1. **Create main page component** (3 hours)
   ```javascript
   // src/pages/RestaurantTicketsPage.js
   // Main container with navigation
   ```

2. **Preview table component** (3 hours)
   ```javascript
   // src/components/restaurant-tickets/TicketPreviewTable.js
   // Sortable, filterable data table
   ```

3. **Generation form** (2 hours)
   ```javascript
   // src/components/restaurant-tickets/GenerationForm.js
   // Month/year selector, validation
   ```

4. **Matricule mapping modal** (2 hours)
   ```javascript
   // src/components/restaurant-tickets/MatriculeMappingModal.js
   // Edit and bulk import UI
   ```

**Acceptance Criteria**:
- [ ] Responsive design on all devices
- [ ] Intuitive user flow
- [ ] Real-time validation
- [ ] Loading states handled

#### Task 4.2: Frontend Integration
**Persona**: Frontend Developer  
**Estimated Time**: 8 hours  
**Dependencies**: Task 4.1  
**MCP Context**: API integration patterns, state management

**Implementation Steps**:
1. **Create API service** (2 hours)
   ```javascript
   // src/services/restaurantTicket.service.js
   ```

2. **State management** (2 hours)
   - Preview data state
   - Generation progress
   - Error handling
   - Cache management

3. **File download handling** (2 hours)
   - Secure download flow
   - Progress indication
   - Error recovery
   - Success notification

4. **UI polish** (2 hours)
   - Animations
   - Tooltips
   - Help text
   - Accessibility

**Acceptance Criteria**:
- [ ] Smooth API integration
- [ ] Downloads work reliably
- [ ] Errors shown clearly
- [ ] Accessible to screen readers

### Phase 5: Testing & Deployment (Week 3)

#### Task 5.1: Comprehensive Testing
**Persona**: QA Engineer  
**Estimated Time**: 12 hours  
**Dependencies**: All features complete  
**MCP Context**: Testing best practices, TDD

**Implementation Steps**:
1. **Unit tests** (4 hours)
   - Service layer tests
   - Calculator edge cases
   - CSV format validation
   - API endpoint tests

2. **Integration tests** (4 hours)
   - End-to-end workflows
   - PayFit API mocking
   - File generation tests
   - Database transactions

3. **UI testing** (2 hours)
   - Component tests
   - User flow tests
   - Accessibility tests
   - Cross-browser tests

4. **Performance tests** (2 hours)
   - Load testing
   - Large dataset handling
   - API response times
   - Memory usage

**Acceptance Criteria**:
- [ ] >90% code coverage
- [ ] All edge cases tested
- [ ] Performance benchmarks met
- [ ] No critical bugs

#### Task 5.2: Deployment & Monitoring
**Persona**: DevOps Engineer  
**Estimated Time**: 8 hours  
**Dependencies**: Testing complete  
**MCP Context**: Deployment patterns, monitoring

**Implementation Steps**:
1. **Deployment preparation** (2 hours)
   - Environment variables
   - File storage setup
   - Database migrations
   - Rollback plan

2. **Monitoring setup** (2 hours)
   - API metrics
   - Error tracking
   - File generation stats
   - Performance monitoring

3. **Documentation** (2 hours)
   - User guide
   - Admin guide
   - API documentation
   - Troubleshooting

4. **Production deployment** (2 hours)
   - Staged rollout
   - Smoke tests
   - Monitoring verification
   - User communication

**Acceptance Criteria**:
- [ ] Zero-downtime deployment
- [ ] All monitors active
- [ ] Documentation complete
- [ ] Users trained

## 📋 Complete Task Summary

### Backend Tasks (40 hours)
1. Database schema and migrations - 4h
2. Matricule mapping service - 6h  
3. Working days calculator - 8h
4. CSV generator service - 6h
5. API endpoints - 8h
6. API integration - 6h
7. Backend testing - 2h

### Frontend Tasks (18 hours)
1. UI components - 10h
2. API integration - 8h

### Testing & Deployment (20 hours)
1. Comprehensive testing - 12h
2. Deployment & monitoring - 8h

### Total Estimated Time: 78 hours (~2 weeks)

## 🎯 Success Metrics
- CSV generation accuracy: 100%
- API response time: <500ms
- UI load time: <2s
- Test coverage: >90%
- Zero critical bugs in production
- User satisfaction: >85%

## 🚀 Next Steps
1. Review and approve workflow
2. Assign team members to phases
3. Set up project tracking
4. Begin Phase 1 implementation
5. Schedule daily standups
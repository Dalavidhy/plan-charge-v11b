# 🚀 Guide d'Implémentation - Ticket Restaurant

## 📋 Checklist de Démarrage Immédiat

### Jour 1 - Configuration initiale (AUJOURD'HUI)

#### 1️⃣ Base de données (Backend Dev 1)
```bash
# Créer la migration Alembic
cd /Users/david/Dev-Workspace/plan-charge-v8
alembic revision -m "add_restaurant_ticket_tables"
```

Copier ce contenu dans le fichier de migration :
```python
"""add restaurant ticket tables

Revision ID: 009
Revises: 008
Create Date: 2025-01-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Table configuration tickets restaurant
    op.create_table('restaurant_ticket_configs',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('company_id', postgresql.UUID(), nullable=True),
        sa.Column('default_monthly_tickets', sa.Integer(), server_default='20', nullable=True),
        sa.Column('ticket_value', sa.DECIMAL(precision=10, scale=2), server_default='11.00', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Table mapping matricules
    op.create_table('employee_matricule_mapping',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(), nullable=True),
        sa.Column('payfit_employee_id', postgresql.UUID(), nullable=True),
        sa.Column('matricule_tr', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['payfit_employee_id'], ['payfit_employees.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('matricule_tr')
    )
    
    # Table logs génération
    op.create_table('restaurant_ticket_logs',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('generated_by', postgresql.UUID(), nullable=True),
        sa.Column('file_path', sa.String(length=255), nullable=True),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('total_tickets', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('generated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('sent_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}', nullable=True),
        sa.ForeignKeyConstraint(['generated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes
    op.create_index('idx_matricule_mapping_user', 'employee_matricule_mapping', ['user_id'])
    op.create_index('idx_ticket_logs_period', 'restaurant_ticket_logs', ['year', 'month'])

def downgrade():
    op.drop_index('idx_ticket_logs_period', 'restaurant_ticket_logs')
    op.drop_index('idx_matricule_mapping_user', 'employee_matricule_mapping')
    op.drop_table('restaurant_ticket_logs')
    op.drop_table('employee_matricule_mapping')
    op.drop_table('restaurant_ticket_configs')
```

#### 2️⃣ Models SQLAlchemy (Backend Dev 1)
Créer `app/models/restaurant_ticket.py`:
```python
from sqlalchemy import Column, String, Integer, Boolean, DECIMAL, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

class RestaurantTicketConfig(Base):
    __tablename__ = "restaurant_ticket_configs"
    
    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    company_id = Column(UUID, ForeignKey("companies.id"))
    default_monthly_tickets = Column(Integer, default=20)
    ticket_value = Column(DECIMAL(10, 2), default=11.00)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relations
    company = relationship("Company", back_populates="restaurant_ticket_config")

class EmployeeMatriculeMapping(Base):
    __tablename__ = "employee_matricule_mapping"
    
    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID, ForeignKey("users.id"))
    payfit_employee_id = Column(UUID, ForeignKey("payfit_employees.id"))
    matricule_tr = Column(String(50), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relations
    user = relationship("User", back_populates="matricule_mapping")
    payfit_employee = relationship("PayfitEmployee", back_populates="matricule_mapping")

class RestaurantTicketLog(Base):
    __tablename__ = "restaurant_ticket_logs"
    
    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    generated_by = Column(UUID, ForeignKey("users.id"))
    file_path = Column(String(255))
    employee_count = Column(Integer)
    total_tickets = Column(Integer)
    status = Column(String(50))  # draft, generated, sent
    generated_at = Column(TIMESTAMP, server_default=func.now())
    sent_at = Column(TIMESTAMP)
    metadata = Column(JSONB, default={})
    
    # Relations
    generator = relationship("User", back_populates="restaurant_ticket_logs")
```

#### 3️⃣ Service Matricule (Backend Dev 2)
Créer `app/services/matricule_mapping.py`:
```python
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.restaurant_ticket import EmployeeMatriculeMapping
from app.schemas.restaurant_ticket import MatriculeMappingCreate, MatriculeMappingUpdate

class MatriculeMappingService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_mapping(self, user_id: str, matricule_tr: str) -> EmployeeMatriculeMapping:
        """Créer un nouveau mapping matricule"""
        # Vérifier si le matricule existe déjà
        existing = self.db.query(EmployeeMatriculeMapping).filter(
            EmployeeMatriculeMapping.matricule_tr == matricule_tr
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Ce matricule est déjà utilisé")
        
        # Créer le mapping
        mapping = EmployeeMatriculeMapping(
            user_id=user_id,
            matricule_tr=matricule_tr
        )
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        
        return mapping
    
    def get_mapping_by_user(self, user_id: str) -> Optional[EmployeeMatriculeMapping]:
        """Récupérer le mapping d'un utilisateur"""
        return self.db.query(EmployeeMatriculeMapping).filter(
            EmployeeMatriculeMapping.user_id == user_id,
            EmployeeMatriculeMapping.is_active == True
        ).first()
    
    def bulk_import_mappings(self, mappings: List[dict]) -> dict:
        """Importer plusieurs mappings depuis un CSV"""
        success = 0
        errors = []
        
        for mapping_data in mappings:
            try:
                self.create_mapping(
                    user_id=mapping_data['user_id'],
                    matricule_tr=mapping_data['matricule']
                )
                success += 1
            except Exception as e:
                errors.append({
                    'matricule': mapping_data.get('matricule'),
                    'error': str(e)
                })
        
        return {
            'success': success,
            'errors': errors,
            'total': len(mappings)
        }
```

### 🎯 Actions immédiates à faire :

1. **Exécuter la migration** :
   ```bash
   alembic upgrade head
   ```

2. **Tester la base de données** :
   ```bash
   python -c "from app.models.restaurant_ticket import *; print('Models OK')"
   ```

3. **Lancer les tests unitaires** :
   ```bash
   pytest tests/unit/test_restaurant_ticket.py -v
   ```

### 📅 Planning des prochains jours :

**Jour 2** : 
- Working Days Calculator (PayFit integration)
- CSV Generator Service
- Début Frontend (mockups)

**Jour 3** :
- API Endpoints
- Frontend components
- Tests unitaires

**Jour 4-5** :
- Integration Frontend/Backend
- Tests d'intégration
- Documentation

### 🛠️ Environnement de développement

1. **Backend** :
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **Frontend** :
   ```bash
   cd frontend
   npm start
   ```

3. **Tests** :
   ```bash
   # Backend
   pytest

   # Frontend
   npm test
   ```

### 📞 Support & Questions

- **Documentation technique** : `/docs/feature-ticket-restau.workflow.md`
- **Suivi des tâches** : `/docs/feature-ticket-restau.tasks.md`
- **Questions** : Créer une issue avec le tag `ticket-restaurant`

---

**IMPORTANT** : Commencez par la migration de base de données MAINTENANT. C'est le point de départ critique pour tout le reste.
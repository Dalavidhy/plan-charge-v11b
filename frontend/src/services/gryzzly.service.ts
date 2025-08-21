/**
 * Gryzzly service for API communication
 */
import api from '../config/api';
import { logger } from '@/utils/logger';

export interface GryzzlyCollaborator {
  id: string;
  gryzzly_id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  matricule?: string;
  department?: string;
  position?: string;
  is_active: boolean;
  is_admin: boolean;
  local_user_id?: string;
  last_synced_at: string;
  created_at: string;
  updated_at: string;
}

export interface GryzzlyProject {
  id: string;
  gryzzly_id: string;
  name: string;
  code?: string;
  description?: string;
  client_name?: string;
  project_type?: string;
  start_date?: string;
  end_date?: string;
  is_active: boolean;
  is_billable: boolean;
  budget_hours?: number;
  budget_amount?: number;
  last_synced_at: string;
  created_at: string;
  updated_at: string;
}

export interface GryzzlyTask {
  id: string;
  gryzzly_id: string;
  project_id: string;
  name: string;
  code?: string;
  description?: string;
  task_type?: string;
  estimated_hours?: number;
  is_active: boolean;
  is_billable: boolean;
  last_synced_at: string;
  created_at: string;
  updated_at: string;
}

export interface GryzzlyDeclaration {
  id: string;
  gryzzly_id: string;
  collaborator_id: string;
  project_id: string;
  task_id?: string;
  date: string;
  duration_hours: number;
  duration_minutes?: number;
  description?: string;
  comment?: string;
  status: string;
  approved_by?: string;
  approved_at?: string;
  is_billable: boolean;
  billing_rate?: number;
  last_synced_at: string;
  created_at: string;
  updated_at: string;
}

export interface GryzzlySyncLog {
  id: string;
  sync_type: string;
  sync_status: string;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  records_synced: number;
  records_created: number;
  records_updated: number;
  records_failed: number;
  error_message?: string;
  triggered_by?: string;
  created_at: string;
}

export interface GryzzlySyncStatus {
  last_sync?: {
    type: string | null;
    status: string | null;
    timestamp: string | null;
    records_synced: number;
  };
  data_counts: {
    collaborators: number;
    projects: number;
    tasks: number;
    declarations: number;
  };
  api_connected: boolean;
}

export interface GryzzlyStats {
  total_collaborators: number;
  active_collaborators: number;
  total_projects: number;
  active_projects: number;
  billable_projects: number;
  total_tasks: number;
  total_declarations: number;
  approved_declarations: number;
  pending_declarations: number;
}

class GryzzlyService {
  // Status and stats
  async getStatus(): Promise<GryzzlySyncStatus> {
    const response = await api.get('/gryzzly/status');
    return response.data;
  }

  async getStats(): Promise<GryzzlyStats> {
    const response = await api.get('/gryzzly/stats');
    return response.data;
  }

  // Connection test
  async testConnection(): Promise<{ status: string; message: string }> {
    try {
      logger.debug('🧪 GryzzlyService: Testing connection to Gryzzly API...');
      const response = await api.post('/gryzzly/sync/test-connection');
      logger.debug('✅ GryzzlyService: Connection test successful', response.data);
      return response.data;
    } catch (error: any) {
      logger.error('❌ GryzzlyService: Connection test failed', error);
      logger.error('📋 Error details:', {
        status: error?.response?.status,
        statusText: error?.response?.statusText,
        data: error?.response?.data,
        message: error?.message
      });
      throw error;
    }
  }

  // Sync triggers
  async syncCollaborators(): Promise<{ status: string; message: string; details?: any }> {
    const response = await api.post('/gryzzly/sync/collaborators');
    return response.data;
  }

  async syncProjects(): Promise<{ status: string; message: string; details?: any }> {
    const response = await api.post('/gryzzly/sync/projects');
    return response.data;
  }

  async syncTasks(): Promise<{ status: string; message: string; details?: any }> {
    const response = await api.post('/gryzzly/sync/tasks');
    return response.data;
  }

  async syncDeclarations(startDate?: string, endDate?: string): Promise<{ status: string; message: string; details?: any }> {
    const response = await api.post('/gryzzly/sync/declarations', {
      start_date: startDate,
      end_date: endDate,
    });
    return response.data;
  }

  async syncFull(): Promise<{ status: string; message: string; details?: any }> {
    const response = await api.post('/gryzzly/sync/full');
    return response.data;
  }

  // Data endpoints
  async getCollaborators(params?: {
    skip?: number;
    limit?: number;
    active_only?: boolean;
  }): Promise<GryzzlyCollaborator[]> {
    const response = await api.get('/gryzzly/collaborators', { params });
    return response.data;
  }

  async getProjects(params?: {
    skip?: number;
    limit?: number;
    active_only?: boolean;
    billable_only?: boolean;
  }): Promise<GryzzlyProject[]> {
    const response = await api.get('/gryzzly/projects', { params });
    return response.data;
  }

  async getTasks(params?: {
    project_id?: string;
    skip?: number;
    limit?: number;
    active_only?: boolean;
  }): Promise<GryzzlyTask[]> {
    const response = await api.get('/gryzzly/tasks', { params });
    return response.data;
  }

  async getDeclarations(params?: {
    collaborator_id?: string;
    project_id?: string;
    start_date?: string;
    end_date?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<GryzzlyDeclaration[]> {
    const response = await api.get('/gryzzly/declarations', { params });
    return response.data;
  }

  async getSyncLogs(params?: {
    sync_type?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<GryzzlySyncLog[]> {
    const response = await api.get('/gryzzly/sync-logs', { params });
    return response.data;
  }
}

export default new GryzzlyService();

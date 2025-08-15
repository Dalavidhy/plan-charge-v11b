/**
 * Payfit service for API communication
 */
import api from '../config/api';

export interface PayfitEmployee {
  id: string;
  payfit_id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  registration_number?: string;
  birth_date?: string;
  gender?: string;
  nationality?: string;
  department?: string;
  position?: string;
  hire_date?: string;
  termination_date?: string;
  is_active: boolean;
  manager_payfit_id?: string;
  local_user_id?: string;
  last_synced_at: string;
  created_at: string;
  updated_at: string;
}

export interface PayfitContract {
  id: string;
  payfit_id: string;
  payfit_employee_id: string;
  employee_first_name?: string;
  employee_last_name?: string;
  employee_email?: string;
  employee_full_name?: string;
  contract_type?: string;
  job_title?: string;
  start_date: string;
  end_date?: string;
  weekly_hours?: number;
  daily_hours?: number;
  annual_hours?: number;
  part_time_percentage?: number;
  is_active: boolean;
  probation_end_date?: string;
  last_synced_at: string;
  created_at: string;
  updated_at: string;
}

export interface PayfitAbsence {
  id: string;
  payfit_id: string;
  payfit_employee_id: string;
  employee_first_name?: string;
  employee_last_name?: string;
  employee_email?: string;
  employee_full_name?: string;
  absence_type: string;
  absence_code?: string;
  start_date: string;
  end_date: string;
  duration_days?: number;
  duration_hours?: number;
  status: string;
  approved_by?: string;
  approved_at?: string;
  reason?: string;
  comment?: string;
  last_synced_at: string;
  created_at: string;
  updated_at: string;
}

export interface PayfitSyncLog {
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

export interface PayfitSyncStatus {
  last_sync?: {
    type: string | null;
    status: string | null;
    timestamp: string | null;
    records_synced: number;
  };
  data_counts: {
    employees: number;
    contracts: number;
    absences: number;
  };
  api_connected: boolean;
}

export interface PayfitStats {
  total_employees: number;
  active_employees: number;
  total_contracts: number;
  active_contracts: number;
  total_absences: number;
  approved_absences: number;
  pending_absences: number;
}

class PayfitService {
  // Status and stats
  async getStatus(): Promise<PayfitSyncStatus> {
    const response = await api.get('/payfit/status');
    return response.data;
  }

  async getStats(): Promise<PayfitStats> {
    const response = await api.get('/payfit/stats');
    return response.data;
  }

  // Connection test
  async testConnection(): Promise<{ status: string; message: string }> {
    try {
      console.log('🧪 PayfitService: Testing connection to Payfit API...');
      const response = await api.post('/payfit/sync/test-connection');
      console.log('✅ PayfitService: Connection test successful', response.data);
      return response.data;
    } catch (error: any) {
      console.error('❌ PayfitService: Connection test failed', error);
      console.error('📋 Error details:', {
        status: error?.response?.status,
        statusText: error?.response?.statusText,
        data: error?.response?.data,
        message: error?.message
      });
      throw error;
    }
  }

  // Sync triggers
  async syncEmployees(): Promise<{ status: string; message: string }> {
    const response = await api.post('/payfit/sync/employees');
    return response.data;
  }

  async syncContracts(): Promise<{ status: string; message: string }> {
    const response = await api.post('/payfit/sync/contracts');
    return response.data;
  }

  async syncAbsences(startDate?: string, endDate?: string): Promise<{ status: string; message: string }> {
    const response = await api.post('/payfit/sync/absences', {
      start_date: startDate,
      end_date: endDate,
    });
    return response.data;
  }

  async syncFull(): Promise<{ status: string; message: string }> {
    const response = await api.post('/payfit/sync/full');
    return response.data;
  }

  // Data endpoints
  async getEmployees(params?: {
    skip?: number;
    limit?: number;
    active_only?: boolean;
  }): Promise<PayfitEmployee[]> {
    const response = await api.get('/payfit/employees', { params });
    return response.data;
  }

  async getEmployee(employeeId: string): Promise<PayfitEmployee> {
    const response = await api.get(`/payfit/employees/${employeeId}`);
    return response.data;
  }

  async getContracts(params?: {
    employee_id?: string;
    active_only?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<PayfitContract[]> {
    const response = await api.get('/payfit/contracts', { params });
    return response.data;
  }

  async getAbsences(params?: {
    employee_id?: string;
    start_date?: string;
    end_date?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<PayfitAbsence[]> {
    const response = await api.get('/payfit/absences', { params });
    return response.data;
  }

  async getSyncLogs(params?: {
    sync_type?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<PayfitSyncLog[]> {
    const response = await api.get('/payfit/sync-logs', { params });
    return response.data;
  }
}

export default new PayfitService();
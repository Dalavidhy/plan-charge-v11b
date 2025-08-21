/**
 * Forecast service for plan de charge predictions
 */
import api from '../config/api';
import { logger } from '@/utils/logger';

export interface ForecastProject {
  id: string;
  gryzzly_id: string;
  name: string;
  code?: string;
  description?: string;
  client_name?: string;
  is_active: boolean;
  is_billable: boolean;
  tasks: ForecastTask[];
}

export interface ForecastTask {
  id: string;
  gryzzly_id: string;
  name: string;
  code?: string;
  description?: string;
  task_type?: string;
  is_active: boolean;
  is_billable: boolean;
}

export interface ForecastEntry {
  id: string;
  project_id: string;
  project_name: string;
  project_code?: string;
  task_id?: string;
  task_name?: string;
  hours: number;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ForecastCollaborator {
  collaborator_id: string;
  collaborator_name: string;
  forecasts: Record<string, ForecastEntry[]>; // date -> forecast entries
}

export interface ForecastData {
  year: number;
  month: number;
  start_date: string;
  end_date: string;
  collaborators: ForecastCollaborator[];
}

export interface CreateForecastParams {
  collaborator_id: string;
  project_id: string;
  task_id?: string;
  date: string;
  hours: number;
  description?: string;
}

export interface BatchCreateForecastParams {
  collaborator_id: string;
  project_id: string;
  task_id?: string;
  start_date: string;
  end_date: string;
  hours_per_day?: number;
  description?: string;
}

export interface UpdateForecastParams {
  hours: number;
  description?: string;
}

export interface ForecastGroup {
  forecast_ids: string[];
  collaborator_id: string;
  project_id: string;
  project_name?: string;
  task_id?: string;
  task_name?: string;
  start_date: string;
  end_date: string;
  hours_per_day: number;
  description?: string;
  total_days: number;
}

class ForecastService {
  /**
   * Get active projects with their tasks for forecast selection
   */
  async getProjectsWithTasks(activeOnly: boolean = true): Promise<ForecastProject[]> {
    try {
      const response = await api.get('/collaborators/projects-with-tasks', {
        params: { active_only: activeOnly }
      });
      return response.data;
    } catch (error) {
      logger.error('Error fetching projects with tasks:', error);
      throw error;
    }
  }

  /**
   * Create a single forecast entry
   */
  async createForecast(params: CreateForecastParams): Promise<{ id: string; message: string; action: string }> {
    try {
      const response = await api.post('/collaborators/forecast', params);
      return response.data;
    } catch (error) {
      logger.error('Error creating forecast:', error);
      throw error;
    }
  }

  /**
   * Create multiple forecast entries for a date range
   */
  async createForecastBatch(params: BatchCreateForecastParams): Promise<{ message: string; created: number; updated: number; total_days: number }> {
    try {
      const response = await api.post('/collaborators/forecast/batch', params);
      return response.data;
    } catch (error) {
      logger.error('Error creating forecast batch:', error);
      throw error;
    }
  }

  /**
   * Get forecast entries for a specific month
   */
  async getForecasts(year: number, month: number, collaboratorId?: string): Promise<ForecastData> {
    try {
      const response = await api.get('/collaborators/forecast', {
        params: {
          year,
          month,
          collaborator_id: collaboratorId
        }
      });
      return response.data;
    } catch (error) {
      logger.error('Error fetching forecasts:', error);
      throw error;
    }
  }

  /**
   * Update a specific forecast entry
   */
  async updateForecast(forecastId: string, params: UpdateForecastParams): Promise<{ id: string; message: string }> {
    try {
      const response = await api.put(`/collaborators/forecast/${forecastId}`, params);
      return response.data;
    } catch (error) {
      logger.error('Error updating forecast:', error);
      throw error;
    }
  }

  /**
   * Delete a specific forecast entry
   */
  async deleteForecast(forecastId: string): Promise<{ message: string }> {
    try {
      const response = await api.delete(`/collaborators/forecast/${forecastId}`);
      return response.data;
    } catch (error) {
      logger.error('Error deleting forecast:', error);
      throw error;
    }
  }

  /**
   * Get forecast for a specific collaborator and date
   */
  getForecastForDate(forecasts: ForecastData, collaboratorId: string, date: string): ForecastEntry[] {
    const collaborator = forecasts.collaborators.find(c => c.collaborator_id === collaboratorId);
    if (!collaborator) return [];
    return collaborator.forecasts[date] || [];
  }

  /**
   * Calculate total forecast hours for a collaborator in a month
   */
  calculateMonthlyTotal(forecasts: ForecastData, collaboratorId: string): number {
    const collaborator = forecasts.collaborators.find(c => c.collaborator_id === collaboratorId);
    if (!collaborator) return 0;
    
    let total = 0;
    Object.values(collaborator.forecasts).forEach(dayForecasts => {
      dayForecasts.forEach(forecast => {
        total += forecast.hours;
      });
    });
    
    return total;
  }

  /**
   * Get the group of forecasts that were created together
   */
  async getForecastGroup(forecastId: string): Promise<ForecastGroup> {
    try {
      const response = await api.get(`/collaborators/forecast/${forecastId}/group`);
      return response.data;
    } catch (error) {
      logger.error('Error fetching forecast group:', error);
      throw error;
    }
  }

  /**
   * Delete a group of forecast entries
   */
  async deleteForecastGroup(forecastIds: string[]): Promise<{ message: string; deleted_count: number }> {
    try {
      const response = await api.delete('/collaborators/forecast/group', {
        data: { forecast_ids: forecastIds }
      });
      return response.data;
    } catch (error) {
      logger.error('Error deleting forecast group:', error);
      throw error;
    }
  }
}

export default new ForecastService();
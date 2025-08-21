import api from '../config/api';
import { logger } from '@/utils/logger';

export interface TREmployee {
  email: string;
  matricule: string;
  first_name: string;
  last_name: string;
  year: number;
  month: number;
  working_days: number;
  absence_days: number;
  tr_rights: number;
  absences: TRAbsence[];
  holidays: string[];
}

export interface TRAbsence {
  type: string;
  start_date: string;
  end_date: string;
  working_days_in_month: number;
  status: string;
}

export interface TRMonthData {
  year: number;
  month: number;
  working_days: number;
  holidays: string[];
  employees: TREmployee[];
}

export interface WorkingDaysData {
  year: number;
  month: number;
  working_days_count: number;
  working_days: string[];
  holidays: string[];
  weekends: string[];
  total_days: number;
}

class TRService {
  /**
   * Get working days information for a given month
   */
  async getWorkingDays(year: number, month: number): Promise<WorkingDaysData> {
    try {
      const response = await api.get<WorkingDaysData>(
        `/tr/working-days/${year}/${month}`
      );
      return response.data;
    } catch (error) {
      logger.error('Error fetching working days:', error);
      throw error;
    }
  }

  /**
   * Get TR rights for all employees for a given month
   */
  async getTRRights(year: number, month: number): Promise<TRMonthData> {
    try {
      const response = await api.get<TRMonthData>(
        `/tr/rights/${year}/${month}`
      );
      return response.data;
    } catch (error) {
      logger.error('Error fetching TR rights:', error);
      throw error;
    }
  }

  /**
   * Get TR rights for a specific employee
   */
  async getEmployeeTRRights(year: number, month: number, email: string): Promise<TREmployee> {
    try {
      const response = await api.get<TREmployee>(
        `/tr/rights/${year}/${month}/${email}`
      );
      return response.data;
    } catch (error) {
      logger.error('Error fetching employee TR rights:', error);
      throw error;
    }
  }

  /**
   * Export TR rights as CSV
   */
  async exportTRRights(year: number, month: number): Promise<Blob> {
    try {
      const response = await api.get(
        `/tr/export/${year}/${month}`,
        {
          responseType: 'blob',
          headers: {
            'Accept': 'text/csv'
          }
        }
      );
      return response.data;
    } catch (error) {
      logger.error('Error exporting TR rights:', error);
      throw error;
    }
  }

  /**
   * Download TR rights CSV file
   */
  async downloadTRRights(year: number, month: number): Promise<void> {
    try {
      const blob = await this.exportTRRights(year, month);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `titres-restaurant-${year}-${month.toString().padStart(2, '0')}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      logger.error('Error downloading TR rights:', error);
      throw error;
    }
  }
}

const trService = new TRService();
export default trService;

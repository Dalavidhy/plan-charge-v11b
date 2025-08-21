/**
 * Plan de Charge service for fetching aggregated data
 */
import api from '../config/api';
import { logger } from '@/utils/logger';

export interface PlanChargeDeclaration {
  project_id: string;
  project_name: string;
  project_code?: string;
  hours: number;
  description?: string;
  status: string;
  is_billable: boolean;
}

export interface PlanChargeAbsence {
  type: string;
  start_date: string;
  end_date: string;
  duration_days?: number;
  status: string;
}

export interface PlanChargeCollaborator {
  collaborator_id: string;
  name: string;
  email: string;
  matricule?: string;
  gryzzly_id?: string;
  payfit_id?: string;
  declarations: Record<string, PlanChargeDeclaration[]>; // date -> declarations
  absences: PlanChargeAbsence[];
}

export interface PlanChargeData {
  year: number;
  month: number;
  start_date: string;
  end_date: string;
  collaborators: PlanChargeCollaborator[];
}

class PlanChargeService {
  /**
   * Get plan de charge data for a specific month
   */
  async getPlanCharge(year: number, month: number): Promise<PlanChargeData> {
    try {
      const response = await api.get('/collaborators/plan-charge', {
        params: { year, month }
      });
      return response.data;
    } catch (error) {
      logger.error('Error fetching plan de charge data:', error);
      throw error;
    }
  }

  /**
   * Calculate total hours for a specific day
   * Handles the overlap logic: if absence exists, show 7h max for absence
   * but allow cumulative project hours
   */
  calculateDayHours(
    declarations: PlanChargeDeclaration[],
    absences: PlanChargeAbsence[],
    date: string
  ): {
    hasAbsence: boolean;
    absenceHours: number;
    projectHours: Record<string, number>;
    totalProjectHours: number;
  } {
    // Check if there's an absence on this date
    const hasAbsence = absences.some(absence => {
      const absStart = new Date(absence.start_date);
      const absEnd = new Date(absence.end_date);
      const checkDate = new Date(date);
      return checkDate >= absStart && checkDate <= absEnd;
    });

    // Group project hours
    const projectHours: Record<string, number> = {};
    let totalProjectHours = 0;

    if (declarations) {
      declarations.forEach(decl => {
        const projectName = decl.project_name;
        if (!projectHours[projectName]) {
          projectHours[projectName] = 0;
        }
        projectHours[projectName] += decl.hours;
        totalProjectHours += decl.hours;
      });
    }

    return {
      hasAbsence,
      absenceHours: hasAbsence ? 7 : 0,
      projectHours,
      totalProjectHours
    };
  }

  /**
   * Check if a date is within an absence period
   */
  isDateInAbsence(date: string, absences: PlanChargeAbsence[]): boolean {
    const checkDate = new Date(date);
    return absences.some(absence => {
      const absStart = new Date(absence.start_date);
      const absEnd = new Date(absence.end_date);
      return checkDate >= absStart && checkDate <= absEnd;
    });
  }

  /**
   * Get absence type for a specific date
   */
  getAbsenceTypeForDate(date: string, absences: PlanChargeAbsence[]): string | null {
    const checkDate = new Date(date);
    const absence = absences.find(abs => {
      const absStart = new Date(abs.start_date);
      const absEnd = new Date(abs.end_date);
      return checkDate >= absStart && checkDate <= absEnd;
    });
    return absence ? absence.type : null;
  }

  /**
   * Format hours for display
   */
  formatHours(hours: number): string {
    if (hours === 0) return '';
    if (hours % 1 === 0) return hours.toString();
    return hours.toFixed(1);
  }
}

export default new PlanChargeService();

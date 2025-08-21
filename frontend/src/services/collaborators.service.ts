/**
 * Collaborators service for unified employee management
 */
import api from '../config/api';
import { logger } from '@/utils/logger';

export interface Collaborator {
  id: string;
  nom: string;
  email: string;
  matricule?: string;
  department?: string;
  position?: string;
  actif: boolean;
  eligibleTR: boolean;
  source: 'gryzzly' | 'payfit' | 'both';
  gryzzly_id?: string;
  payfit_id?: string;
  has_active_contract: boolean;
  last_synced_at?: string;
}

export interface CollaboratorStats {
  total_collaborators: number;
  active_collaborators: number;
  gryzzly: {
    total: number;
    active: number;
  };
  payfit: {
    total: number;
    active: number;
  };
  eligible_tr: number;
  active_contracts: number;
}

class CollaboratorsService {
  /**
   * Get all collaborators (unified from Gryzzly and Payfit)
   */
  async getCollaborators(activeOnly: boolean = false): Promise<Collaborator[]> {
    try {
      const params = new URLSearchParams();
      if (activeOnly) {
        params.append('active_only', 'true');
      }
      
      const response = await api.get(`/collaborators?${params.toString()}`);
      return response.data;
    } catch (error) {
      logger.error('Error fetching collaborators:', error);
      throw error;
    }
  }

  /**
   * Update collaborator properties
   */
  async updateCollaborator(
    id: string, 
    updates: { actif?: boolean; eligibleTR?: boolean; matricule?: string }
  ): Promise<{ success: boolean; message: string }> {
    try {
      const response = await api.patch(`/collaborators/${id}`, updates);
      return response.data;
    } catch (error) {
      logger.error('Error updating collaborator:', error);
      throw error;
    }
  }

  /**
   * Toggle active status
   */
  async toggleActive(id: string, currentStatus: boolean): Promise<{ success: boolean }> {
    try {
      const response = await this.updateCollaborator(id, { actif: !currentStatus });
      return response;
    } catch (error) {
      logger.error('Error toggling active status:', error);
      throw error;
    }
  }

  /**
   * Toggle TR eligibility (Note: This might be restricted based on contracts)
   */
  async toggleEligible(id: string, currentStatus: boolean): Promise<{ success: boolean }> {
    try {
      const response = await this.updateCollaborator(id, { eligibleTR: !currentStatus });
      return response;
    } catch (error) {
      logger.error('Error toggling TR eligibility:', error);
      throw error;
    }
  }

  /**
   * Get collaborator statistics
   */
  async getStats(): Promise<CollaboratorStats> {
    try {
      const response = await api.get('/collaborators/stats');
      return response.data;
    } catch (error) {
      logger.error('Error fetching collaborator stats:', error);
      throw error;
    }
  }

  /**
   * Search collaborators by name or email
   */
  filterCollaborators(collaborators: Collaborator[], searchTerm: string): Collaborator[] {
    if (!searchTerm) return collaborators;
    
    const term = searchTerm.toLowerCase();
    return collaborators.filter(collab => 
      collab.nom.toLowerCase().includes(term) ||
      collab.email.toLowerCase().includes(term) ||
      (collab.matricule && collab.matricule.toLowerCase().includes(term))
    );
  }

  /**
   * Group collaborators by department
   */
  groupByDepartment(collaborators: Collaborator[]): Record<string, Collaborator[]> {
    return collaborators.reduce((acc, collab) => {
      const dept = collab.department || 'Sans département';
      if (!acc[dept]) {
        acc[dept] = [];
      }
      acc[dept].push(collab);
      return acc;
    }, {} as Record<string, Collaborator[]>);
  }

  /**
   * Get collaborators eligible for TR
   */
  getEligibleForTR(collaborators: Collaborator[]): Collaborator[] {
    return collaborators.filter(collab => collab.eligibleTR && collab.actif);
  }

  /**
   * Export collaborators to CSV
   */
  exportToCSV(collaborators: Collaborator[]): string {
    const headers = ['Matricule', 'Nom', 'Email', 'Département', 'Poste', 'Actif', 'Éligible TR', 'Source'];
    const rows = collaborators.map(collab => [
      collab.matricule || '',
      collab.nom,
      collab.email,
      collab.department || '',
      collab.position || '',
      collab.actif ? 'Oui' : 'Non',
      collab.eligibleTR ? 'Oui' : 'Non',
      collab.source
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    return csvContent;
  }

  /**
   * Download collaborators as CSV file
   */
  downloadCSV(collaborators: Collaborator[], filename: string = 'collaborateurs.csv'): void {
    const csv = this.exportToCSV(collaborators);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

export default new CollaboratorsService();
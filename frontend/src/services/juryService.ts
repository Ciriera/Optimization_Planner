import { api } from './authService';

export interface JuryMember {
  id: number;
  name: string;
  type: string;
  role: string;
}

export interface ProjectJury {
  project_id: number;
  project_title: string;
  responsible_instructor: JuryMember | null;
  jury_members: JuryMember[];
  total_jury_count: number;
}

export interface JuryAssignmentRequest {
  project_id: number;
  jury_member_ids: number[];
}

export interface BatchJuryAssignmentRequest {
  project_assignments: JuryAssignmentRequest[];
}

export interface JuryAssignmentResponse {
  project_id: number;
  jury_members: JuryMember[];
  message: string;
}

export interface BatchJuryAssignmentResponse {
  total_processed: number;
  results: Array<{
    project_id: number;
    status: string;
    jury_count?: number;
    message?: string;
  }>;
  message: string;
}

class JuryService {
  /**
   * Projeye jüri üyelerini ata
   */
  async assignJuryToProject(projectId: number, juryMemberIds: number[]): Promise<JuryAssignmentResponse> {
    const response = await api.post(`/projects/${projectId}/jury`, {
      jury_member_ids: juryMemberIds
    });
    return response.data;
  }

  /**
   * Projenin jüri üyelerini getir
   */
  async getProjectJury(projectId: number): Promise<ProjectJury> {
    const response = await api.get(`/projects/${projectId}/jury`);
    return response.data;
  }

  /**
   * Projeden jüri üyesini kaldır
   */
  async removeJuryMember(projectId: number, instructorId: number): Promise<{ message: string }> {
    const response = await api.delete(`/projects/${projectId}/jury/${instructorId}`);
    return response.data;
  }

  /**
   * Birden fazla projeye toplu jüri ataması yap
   */
  async batchAssignJury(assignments: JuryAssignmentRequest[]): Promise<BatchJuryAssignmentResponse> {
    const response = await api.post('/projects/batch-assign-jury', {
      project_assignments: assignments
    });
    return response.data;
  }

  /**
   * Tüm projelerin jüri bilgilerini getir
   */
  async getAllProjectsJury(): Promise<ProjectJury[]> {
    // Bu endpoint mevcut değil, projeleri tek tek alacağız
    // Alternatif olarak projects endpoint'ini güncelleyebiliriz
    throw new Error('getAllProjectsJury not implemented - use getProjectJury for individual projects');
  }

  /**
   * Jüri üyesi olarak uygun instructor'ları getir
   */
  async getEligibleJuryMembers(): Promise<JuryMember[]> {
    // Instructors endpoint'ini kullanacağız
    const response = await api.get('/instructors/');
    const instructors = response.data;
    
    // Jüri üyesi olarak uygun olanları filtrele
    return instructors.filter((instructor: any) => {
      const name = instructor.name || '';
      const type = instructor.type || '';
      // Prof. Dr., Doç. Dr., Dr. Öğr. Üyesi unvanlı hocaları dahil et
      return name.includes('Prof. Dr.') || name.includes('Doç. Dr.') || name.includes('Dr. Öğr. Üyesi') ||
             type === 'instructor' || type === 'associate' || type === 'assistant';
    }).map((instructor: any) => ({
      id: instructor.id,
      name: instructor.name,
      type: instructor.type,
      role: 'jury_member'
    }));
  }
}

export const juryService = new JuryService();

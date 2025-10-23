import { api } from './authService';

export interface Project {
  id: number;
  title: string;
  type: string; // 'ara' | 'bitirme' (backend)
  status?: string | null;
  responsible_instructor_id: number;
}

export interface ProjectCreateInput {
  title: string;
  type: string; // frontend value
  responsible_instructor_id: number;
}

export const projectService = {
  async list() {
    const res = await api.get<Project[]>('/projects/');
    return res.data;
  },

  async create(data: ProjectCreateInput) {
    const normalized = {
      title: data.title,
      type: data.type, // Artık zaten 'final' veya 'interim' kullanıyoruz
      responsible_instructor_id: data.responsible_instructor_id,
    };
    const res = await api.post<Project>('/projects/', normalized);
    return res.data;
  },
};


import { api } from './authService';

export interface Instructor {
  id: number;
  name: string;
  type?: string;
  bitirme_count?: number;
  ara_count?: number;
  total_load?: number;
  total_jury_count?: number;
}

export interface InstructorCreateInput {
  name: string;
  type: string;
}

export const instructorService = {
  async list() {
    const res = await api.get<Instructor[]>('/instructors/');
    return res.data;
  },

  async create(data: InstructorCreateInput) {
    const res = await api.post<Instructor>('/instructors/', data);
    return res.data;
  },
};


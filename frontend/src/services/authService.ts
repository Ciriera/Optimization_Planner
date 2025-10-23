import axios from 'axios';

const API_BASE_URL = '/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers = config.headers || {};
      (config.headers as any).Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_superuser: boolean;
}

class AuthService {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      (api.defaults.headers.common as any)['Authorization'] = `Bearer ${token}`;
    } else {
      delete (api.defaults.headers.common as any)['Authorization'];
    }
  }

  async login(email: string, password: string): Promise<{ access_token: string; user: User }> {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await api.post('/auth/login/access-token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    const { access_token } = response.data;

    // Set token immediately so subsequent requests include Authorization
    this.setToken(access_token);
    localStorage.setItem('token', access_token);

    // Fetch current user via POST
    const userResponse = await api.post('/auth/test-token');
    const user = userResponse.data;

    return { access_token, user };
  }

  async getCurrentUser(): Promise<User> {
    const response = await api.post('/auth/test-token');
    return response.data;
  }

  async logout(): Promise<void> {
    this.setToken(null);
    localStorage.removeItem('token');
    // Clear all axios headers
    delete (api.defaults.headers.common as any)['Authorization'];
  }
}

export const authService = new AuthService();
export { api };

import api from './api';
import { User, AuthResponse, RegisterData, LoginData } from '../types/auth';

export const authService = {
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/register', data);
    if (response.data.access_token) {
      sessionStorage.setItem('projectdna_token', response.data.access_token);
    }
    return response.data;
  },

  async login(data: LoginData): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/login', data);
    if (response.data.access_token) {
      sessionStorage.setItem('projectdna_token', response.data.access_token);
    }
    return response.data;
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } finally {
      sessionStorage.removeItem('projectdna_token');
    }
  },

  async getMe(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data;
  }
};


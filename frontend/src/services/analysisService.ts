import api from './api';
import {
  ProjectAnalysis,
  ProjectAnalysisListResponse,
  DashboardAnalytics,
} from '../types/analysis';

export const analysisService = {
  async analyzeProject(projectId: string): Promise<ProjectAnalysis> {
    const response = await api.post<ProjectAnalysis>(`/projects/${projectId}/analyze`, null, {
      timeout: 90000 // Structured LLM generation may take 15-30 seconds
    });
    return response.data;
  },

  async getLatestAnalysis(projectId: string, version?: number): Promise<ProjectAnalysis> {
    const params = version ? { version } : {};
    const response = await api.get<ProjectAnalysis>(`/projects/${projectId}/analysis`, { params });
    return response.data;
  },

  async getAnalysisHistory(projectId: string): Promise<ProjectAnalysisListResponse> {
    const response = await api.get<ProjectAnalysisListResponse>(`/projects/${projectId}/analyses`);
    return response.data;
  },

  async getDashboardStats(): Promise<DashboardAnalytics> {
    const response = await api.get<DashboardAnalytics>('/analyses/dashboard/stats');
    return response.data;
  },

  async getDiagnostics(): Promise<{
    status: string;
    detected: boolean;
    configured: boolean;
    client_initialized: boolean;
    configured_model: string;
    key_length: number;
    init_error?: string | null;
  }> {
    const response = await api.get('/analysis/diagnostics');
    return response.data;
  }
};


import api from './api';
import {
  RepositoryAnalysisRequest,
  RepositoryAnalysisBatchResponse,
  RepositoryAnalysisListResponse,
  RepositoryAnalysis,
  InnovationGapListResponse,
  RepositoryAnalysisStats,
} from '../types/repositoryAnalysis';

export const repositoryAnalysisService = {
  async analyzeRepositories(
    projectId: string,
    payload?: RepositoryAnalysisRequest
  ): Promise<RepositoryAnalysisBatchResponse> {
    const response = await api.post<RepositoryAnalysisBatchResponse>(
      `/projects/${projectId}/github/analyze`,
      payload || {}
    );
    return response.data;
  },

  async getStoredAnalyses(
    projectId: string,
    page: number = 1,
    pageSize: number = 10
  ): Promise<RepositoryAnalysisListResponse> {
    const response = await api.get<RepositoryAnalysisListResponse>(
      `/projects/${projectId}/github/analysis`,
      { params: { page, page_size: pageSize } }
    );
    return response.data;
  },

  async getSingleAnalysis(
    projectId: string,
    analysisId: string
  ): Promise<RepositoryAnalysis> {
    const response = await api.get<RepositoryAnalysis>(
      `/projects/${projectId}/github/analysis/${analysisId}`
    );
    return response.data;
  },

  async getInnovationGaps(
    projectId: string,
    priority?: string,
    category?: string
  ): Promise<InnovationGapListResponse> {
    const params: Record<string, string> = {};
    if (priority) params.priority = priority;
    if (category) params.category = category;

    const response = await api.get<InnovationGapListResponse>(
      `/projects/${projectId}/github/innovation-gaps`,
      { params }
    );
    return response.data;
  },

  async getAnalysisStats(
    projectId: string
  ): Promise<RepositoryAnalysisStats> {
    const response = await api.get<RepositoryAnalysisStats>(
      `/projects/${projectId}/github/analysis/stats`
    );
    return response.data;
  },
};


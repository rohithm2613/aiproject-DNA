import api from './api';
import {
  ResearchSearchRequest,
  ResearchSearchResponse,
  ResearchListResponse,
  ResearchStatsResponse,
  ResearchFilterParams,
} from '../types/research';

export const researchService = {
  async searchResearchPapers(
    projectId: string,
    payload?: ResearchSearchRequest
  ): Promise<ResearchSearchResponse> {
    const response = await api.post<ResearchSearchResponse>(
      `/projects/${projectId}/research/search`,
      payload || {}
    );
    return response.data;
  },

  async getStoredPapers(
    projectId: string,
    params?: ResearchFilterParams
  ): Promise<ResearchListResponse> {
    const response = await api.get<ResearchListResponse>(
      `/projects/${projectId}/research`,
      { params }
    );
    return response.data;
  },

  async getResearchStats(projectId: string): Promise<ResearchStatsResponse> {
    const response = await api.get<ResearchStatsResponse>(
      `/projects/${projectId}/research/stats`
    );
    return response.data;
  },
};


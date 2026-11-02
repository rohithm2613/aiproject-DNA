import api from './api';
import {
  Patent,
  PatentSearchRequest,
  PatentSearchResponse,
  PatentListResponse,
  PatentStatsResponse,
  PatentAnalyzeRequest,
  PatentAnalysisResponse,
  PatentEvidenceManifestItem,
} from '../types/patent';

export interface PatentFilterParams {
  page?: number;
  page_size?: number;
  jurisdiction?: string;
  provider?: string;
  search_query?: string;
  sort_by?: 'similarity' | 'publication_date' | 'created_at';
}

export const patentService = {
  async searchPatents(
    projectId: string,
    payload?: PatentSearchRequest
  ): Promise<PatentSearchResponse> {
    const response = await api.post<PatentSearchResponse>(
      `/projects/${projectId}/patents/search`,
      payload || {}
    );
    return response.data;
  },

  async getPatents(
    projectId: string,
    params?: PatentFilterParams
  ): Promise<PatentListResponse> {
    const response = await api.get<PatentListResponse>(
      `/projects/${projectId}/patents`,
      { params }
    );
    return response.data;
  },

  async getPatentStats(projectId: string): Promise<PatentStatsResponse> {
    const response = await api.get<PatentStatsResponse>(
      `/projects/${projectId}/patents/stats`
    );
    return response.data;
  },

  async getPatentById(
    projectId: string,
    patentId: string
  ): Promise<Patent> {
    const response = await api.get<Patent>(
      `/projects/${projectId}/patents/${patentId}`
    );
    return response.data;
  },

  async analyzePatents(
    projectId: string,
    payload?: PatentAnalyzeRequest
  ): Promise<PatentAnalysisResponse> {
    const response = await api.post<PatentAnalysisResponse>(
      `/projects/${projectId}/patents/analyze`,
      payload || {}
    );
    return response.data;
  },

  async getPatentAnalysis(projectId: string): Promise<PatentAnalysisResponse> {
    const response = await api.get<PatentAnalysisResponse>(
      `/projects/${projectId}/patents/analysis`
    );
    return response.data;
  },

  async getPatentEvidence(
    projectId: string
  ): Promise<PatentEvidenceManifestItem[]> {
    const response = await api.get<PatentEvidenceManifestItem[]>(
      `/projects/${projectId}/patents/evidence`
    );
    return response.data;
  },
};


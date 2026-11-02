import api from './api';
import {
  EmbeddingGenerateRequest,
  EmbeddingGenerateResponse,
  CrossSourceSimilarityResponse,
  SimilarityStatsResponse,
} from '../types/embedding';

export const embeddingService = {
  async generateEmbeddings(
    projectId: string,
    payload?: EmbeddingGenerateRequest
  ): Promise<EmbeddingGenerateResponse> {
    const response = await api.post<EmbeddingGenerateResponse>(
      `/projects/${projectId}/embeddings/generate`,
      payload || {}
    );
    return response.data;
  },

  async getSemanticSimilarities(
    projectId: string,
    filters?: {
      source_type?: string;
      min_similarity?: number;
      limit?: number;
    }
  ): Promise<CrossSourceSimilarityResponse> {
    const params: Record<string, any> = {};
    if (filters?.source_type && filters.source_type !== 'all') {
      params.source_type = filters.source_type;
    }
    if (filters?.min_similarity !== undefined && filters.min_similarity !== null) {
      params.min_similarity = filters.min_similarity;
    }
    if (filters?.limit) {
      params.limit = filters.limit;
    }

    const response = await api.get<CrossSourceSimilarityResponse>(
      `/projects/${projectId}/similarity`,
      { params }
    );
    return response.data;
  },

  async getSimilarityStats(projectId: string): Promise<SimilarityStatsResponse> {
    const response = await api.get<SimilarityStatsResponse>(
      `/projects/${projectId}/similarity/stats`
    );
    return response.data;
  },
};


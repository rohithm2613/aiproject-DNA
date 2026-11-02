import api from './api';
import {
  GitHubSearchRequest,
  GitHubSearchResponse,
  GitHubRepositoryListResponse,
  GitHubStatsResponse,
  GitHubFilterParams,
} from '../types/github';

export const githubService = {
  async searchGitHubRepositories(
    projectId: string,
    payload?: GitHubSearchRequest
  ): Promise<GitHubSearchResponse> {
    const response = await api.post<GitHubSearchResponse>(
      `/projects/${projectId}/github/search`,
      payload || {}
    );
    return response.data;
  },

  async getStoredRepositories(
    projectId: string,
    params?: GitHubFilterParams
  ): Promise<GitHubRepositoryListResponse> {
    const response = await api.get<GitHubRepositoryListResponse>(
      `/projects/${projectId}/github`,
      { params }
    );
    return response.data;
  },

  async getRepositoryStats(projectId: string): Promise<GitHubStatsResponse> {
    const response = await api.get<GitHubStatsResponse>(
      `/projects/${projectId}/github/stats`
    );
    return response.data;
  },
};


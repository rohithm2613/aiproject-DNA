import api from './api';
import {
  ValidationGenerateRequest,
  ValidationReportResponse,
  ValidationHistoryResponse,
  EvidenceManifestResponse,
} from '../types/validation';

export const validationService = {
  /**
   * Generates or fetches the RAG Research Gap Validation Report.
   */
  async generateValidationReport(
    projectId: string,
    payload?: ValidationGenerateRequest
  ): Promise<ValidationReportResponse> {
    const response = await api.post<ValidationReportResponse>(
      `/projects/${projectId}/validation/generate`,
      payload || {}
    );
    return response.data;
  },

  /**
   * Retrieves the latest validation report for the project.
   */
  async getLatestValidationReport(projectId: string): Promise<ValidationReportResponse> {
    const response = await api.get<ValidationReportResponse>(
      `/projects/${projectId}/validation`
    );
    return response.data;
  },

  /**
   * Retrieves validation report version history and summary metrics.
   */
  async getValidationHistory(projectId: string): Promise<ValidationHistoryResponse> {
    const response = await api.get<ValidationHistoryResponse>(
      `/projects/${projectId}/validation/history`
    );
    return response.data;
  },

  /**
   * Retrieves a specific validation report by ID.
   */
  async getValidationReportById(
    projectId: string,
    reportId: string
  ): Promise<ValidationReportResponse> {
    const response = await api.get<ValidationReportResponse>(
      `/projects/${projectId}/validation/${reportId}`
    );
    return response.data;
  },

  /**
   * Retrieves the normalized evidence manifest with optional report_id filter.
   */
  async getEvidenceManifest(
    projectId: string,
    reportId?: string
  ): Promise<EvidenceManifestResponse> {
    const params: Record<string, string> = {};
    if (reportId) {
      params.report_id = reportId;
    }
    const response = await api.get<EvidenceManifestResponse>(
      `/projects/${projectId}/validation/evidence`,
      { params }
    );
    return response.data;
  },
};


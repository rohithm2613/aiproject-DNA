export type ProjectStatus = 'pending_validation' | 'ready_for_analysis' | 'validated' | 'draft';

export interface Project {
  id: string;
  title: string;
  description: string;
  domain: string;
  technologies: string[];
  objectives?: string | null;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export interface CreateProjectPayload {
  title: string;
  description: string;
  domain: string;
  technologies: string[];
  objectives?: string;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
  page: number;
  limit: number;
}


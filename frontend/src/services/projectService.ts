import api from './api';
import { Project, CreateProjectPayload, ProjectListResponse } from '../types/project';
import { HealthResponse } from '../types/health';

// Initial fallback mock data for resilient display when backend is disconnected
export const FALLBACK_PROJECTS: Project[] = [
  {
    id: "demo-001",
    title: "MedScanAI: Multimodal Radiology Assistant",
    description: "An intelligent medical imaging assistant that cross-references chest X-rays with patient EHR history to detect early pulmonary abnormalities.",
    domain: "Healthcare & AI",
    technologies: ["PyTorch", "FastAPI", "React", "Docker", "DICOM"],
    objectives: "Reduce radiologist diagnosis review time by 35% while maintaining a 98% specificity rate on priority anomalies.",
    status: "ready_for_analysis",
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    updated_at: new Date(Date.now() - 86400000 * 2).toISOString(),
  },
  {
    id: "demo-002",
    title: "EcoGrid: Decentralized Microgrid Load Balancer",
    description: "Autonomous smart-meter orchestration utilizing distributed edge controllers to optimize neighborhood solar power exchange.",
    domain: "CleanTech & IoT",
    technologies: ["Python", "MQTT", "TimeScaleDB", "React", "Tailwind CSS"],
    objectives: "Minimize peak fossil fuel drawdown across residential microgrid clusters using predictive load forecasting.",
    status: "validated",
    created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
    updated_at: new Date(Date.now() - 86400000 * 5).toISOString(),
  },
  {
    id: "demo-003",
    title: "CodeGuardian: Zero-Day Smart Contract Fuzzer",
    description: "Deep reinforcement learning powered security analysis pipeline for EVM smart contracts to detect reentrancy and logic exploits before mainnet deployment.",
    domain: "Cybersecurity & Web3",
    technologies: ["Solidity", "Rust", "Python", "React", "PostgreSQL"],
    objectives: "Automate exploit sequence generation and provide formal verification proofs for high-value DeFi protocols.",
    status: "pending_validation",
    created_at: new Date(Date.now() - 86400000 * 8).toISOString(),
    updated_at: new Date(Date.now() - 86400000 * 8).toISOString(),
  },
  {
    id: "demo-004",
    title: "EduTutor: Real-Time Socratic Code Mentor",
    description: "An interactive programming instructor that provides guided questioning instead of answers to help computer science students build deep algorithmic intuition.",
    domain: "EdTech",
    technologies: ["TypeScript", "FastAPI", "React", "WebSockets", "Node.js"],
    objectives: "Enhance student problem-solving retention without relying on code generation crutches.",
    status: "ready_for_analysis",
    created_at: new Date(Date.now() - 86400000 * 12).toISOString(),
    updated_at: new Date(Date.now() - 86400000 * 12).toISOString(),
  },
];

export const projectService = {
  async getHealth(): Promise<HealthResponse> {
    const response = await api.get<HealthResponse>('/health');
    return response.data;
  },

  async getProjects(params?: {
    search?: string;
    domain?: string;
    status?: string;
    page?: number;
    limit?: number;
  }): Promise<ProjectListResponse> {
    try {
      const response = await api.get<ProjectListResponse>('/projects', { params });
      return response.data;
    } catch {
      // Local fallback filter if API is temporarily unreachable
      let filtered = [...FALLBACK_PROJECTS];
      if (params?.search) {
        const q = params.search.toLowerCase();
        filtered = filtered.filter(
          p => p.title.toLowerCase().includes(q) || p.description.toLowerCase().includes(q) || p.domain.toLowerCase().includes(q)
        );
      }
      if (params?.domain && params.domain !== 'All') {
        filtered = filtered.filter(p => p.domain.toLowerCase().includes(params.domain!.toLowerCase()));
      }
      if (params?.status && params.status !== 'All') {
        filtered = filtered.filter(p => p.status === params.status);
      }
      return {
        items: filtered,
        total: filtered.length,
        page: params?.page || 1,
        limit: params?.limit || 50,
      };
    }
  },

  async getProjectById(id: string): Promise<Project> {
    try {
      const response = await api.get<Project>(`/projects/${id}`);
      return response.data;
    } catch (err) {
      const local = FALLBACK_PROJECTS.find(p => p.id === id);
      if (local) return local;
      throw err;
    }
  },

  async createProject(payload: CreateProjectPayload): Promise<Project> {
    const response = await api.post<Project>('/projects', payload);
    return response.data;
  }
};


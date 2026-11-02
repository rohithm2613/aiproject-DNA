export interface DatabaseHealth {
  status: 'connected' | 'disconnected';
  dialect?: string;
  database?: string;
  error?: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded';
  app_name: string;
  version: string;
  phase: string;
  database: DatabaseHealth;
}


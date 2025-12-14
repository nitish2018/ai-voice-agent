import axios, { AxiosError } from 'axios';
import type {
  Agent,
  AgentCreate,
  AgentUpdate,
  AgentListResponse,
  Call,
  CallTriggerRequest,
  CallListResponse,
  CallResults,
  ApiError,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Error handler
const handleError = (error: unknown): never => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiError>;
    throw new Error(axiosError.response?.data?.detail || axiosError.message);
  }
  throw error;
};

// Agent API
export const agentApi = {
  list: async (skip = 0, limit = 50, activeOnly = false): Promise<AgentListResponse> => {
    try {
      const response = await api.get<AgentListResponse>('/agents', {
        params: { skip, limit, active_only: activeOnly },
      });
      return response.data;
    } catch (error) {
      return handleError(error);
    }
  },

  get: async (id: string): Promise<Agent> => {
    try {
      const response = await api.get<Agent>(`/agents/${id}`);
      return response.data;
    } catch (error) {
      return handleError(error);
    }
  },

  create: async (data: AgentCreate): Promise<Agent> => {
    try {
      const response = await api.post<Agent>('/agents/', data);
      return response.data;
    } catch (error) {
      return handleError(error);
    }
  },

  update: async (id: string, data: AgentUpdate): Promise<Agent> => {
    try {
      const response = await api.put<Agent>(`/agents/${id}`, data);
      return response.data;
    } catch (error) {
      return handleError(error);
    }
  },

  delete: async (id: string): Promise<void> => {
    try {
      await api.delete(`/agents/${id}`);
    } catch (error) {
      handleError(error);
    }
  },
};

// Call API
export const callApi = {
  trigger: async (data: CallTriggerRequest): Promise<Call> => {
    try {
      const response = await api.post<Call>('/calls/trigger', data);
      return response.data;
    } catch (error) {
      return handleError(error);
    }
  },

  list: async (
    skip = 0,
    limit = 50,
    agentId?: string,
    status?: string
  ): Promise<CallListResponse> => {
    try {
      const response = await api.get<CallListResponse>('/calls', {
        params: { skip, limit, agent_id: agentId, status },
      });
      return response.data;
    } catch (error) {
      return handleError(error);
    }
  },

  get: async (id: string): Promise<Call> => {
    try {
      const response = await api.get<Call>(`/calls/${id}`);
      return response.data;
    } catch (error) {
      return handleError(error);
    }
  },

  getResults: async (id: string): Promise<CallResults> => {
    try {
      const response = await api.get<CallResults>(`/calls/${id}/results`);
      return response.data;
    } catch (error) {
      return handleError(error);
    }
  },

  reprocess: async (id: string): Promise<CallResults> => {
    try {
      const response = await api.post<CallResults>(`/calls/${id}/reprocess`);
      return response.data;
    } catch (error) {
      return handleError(error);
    }
  },
};

export default api;

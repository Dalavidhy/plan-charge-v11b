import axios from 'axios';
import { runtimeConfig } from './runtimeConfig';
import { logger } from '@/utils/logger';

// API Base URL - use runtime config (supports both build-time and runtime injection)
const API_BASE_URL = runtimeConfig.apiUrl;

// Debug logging for API configuration
logger.debug('=== API CONFIG DEBUG ===');
logger.debug('Runtime config API URL:', runtimeConfig.apiUrl);
logger.debug('Computed API_BASE_URL:', API_BASE_URL);
logger.debug('Runtime config debug:', runtimeConfig.debugInfo);

// Create axios instance with default config
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    // Debug: Log the final URL being called
    const finalURL = config.baseURL + config.url;
    logger.debug('🌐 API Request:', config.method?.toUpperCase(), finalURL);

    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh and errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retried, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token: newRefreshToken } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', newRefreshToken);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }
    }

    return Promise.reject(error);
  }
);

// Auth API endpoints
export const authAPI = {
  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  register: async (data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }) => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  logout: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      await api.post('/auth/logout', { refresh_token: refreshToken });
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  refreshToken: async (refreshToken: string) => {
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },
};

// Other API endpoints
export const organizationAPI = {
  getAll: async () => {
    const response = await api.get('/orgs');
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get(`/orgs/${id}`);
    return response.data;
  },
};

export const teamAPI = {
  getAll: async () => {
    const response = await api.get('/teams');
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get(`/teams/${id}`);
    return response.data;
  },
};

export const projectAPI = {
  getAll: async () => {
    const response = await api.get('/projects');
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get(`/projects/${id}`);
    return response.data;
  },
};

export const personAPI = {
  getAll: async () => {
    const response = await api.get('/persons');
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get(`/persons/${id}`);
    return response.data;
  },
};

export const allocationAPI = {
  getAll: async () => {
    const response = await api.get('/allocations');
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get(`/allocations/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/allocations', data);
    return response.data;
  },

  update: async (id: string, data: any) => {
    const response = await api.put(`/allocations/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    const response = await api.delete(`/allocations/${id}`);
    return response.data;
  },
};

export default api;

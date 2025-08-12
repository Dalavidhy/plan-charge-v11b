import axios, { AxiosInstance, AxiosError } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000');

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
let accessToken: string | null = localStorage.getItem('accessToken');
let refreshToken: string | null = localStorage.getItem('refreshToken');

// Request interceptor
api.interceptors.request.use(
  (config) => {
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const response = await api.post('/auth/refresh', {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token } = response.data;
        
        accessToken = access_token;
        refreshToken = refresh_token;
        
        localStorage.setItem('accessToken', access_token);
        localStorage.setItem('refreshToken', refresh_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        accessToken = null;
        refreshToken = null;
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    const { access_token, refresh_token, user } = response.data;
    
    accessToken = access_token;
    refreshToken = refresh_token;
    
    localStorage.setItem('accessToken', access_token);
    localStorage.setItem('refreshToken', refresh_token);
    localStorage.setItem('user', JSON.stringify(user));
    
    return response.data;
  },

  logout: async () => {
    try {
      await api.post('/auth/logout', { refresh_token: refreshToken });
    } finally {
      accessToken = null;
      refreshToken = null;
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  changePassword: async (currentPassword: string, newPassword: string) => {
    const response = await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },
};

// Organizations API
export const organizationsApi = {
  list: async (params?: any) => {
    const response = await api.get('/orgs', { params });
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get(`/orgs/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/orgs', data);
    return response.data;
  },

  update: async (id: string, data: any) => {
    const response = await api.patch(`/orgs/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    await api.delete(`/orgs/${id}`);
  },
};

// People API
export const peopleApi = {
  list: async (params?: any) => {
    const response = await api.get('/people', { params });
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get(`/people/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/people', data);
    return response.data;
  },

  update: async (id: string, data: any) => {
    const response = await api.patch(`/people/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    await api.delete(`/people/${id}`);
  },
};

// Teams API
export const teamsApi = {
  list: async (params?: any) => {
    const response = await api.get('/teams', { params });
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get(`/teams/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/teams', data);
    return response.data;
  },

  update: async (id: string, data: any) => {
    const response = await api.patch(`/teams/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    await api.delete(`/teams/${id}`);
  },

  addMember: async (teamId: string, personId: string, data: any) => {
    const response = await api.post(`/teams/${teamId}/members`, { person_id: personId, ...data });
    return response.data;
  },

  removeMember: async (teamId: string, personId: string) => {
    await api.delete(`/teams/${teamId}/members/${personId}`);
  },
};

// Projects API
export const projectsApi = {
  list: async (params?: any) => {
    const response = await api.get('/projects', { params });
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get(`/projects/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/projects', data);
    return response.data;
  },

  update: async (id: string, data: any) => {
    const response = await api.patch(`/projects/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    await api.delete(`/projects/${id}`);
  },
};

// Tasks API
export const tasksApi = {
  list: async (params?: any) => {
    const response = await api.get('/tasks', { params });
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get(`/tasks/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/tasks', data);
    return response.data;
  },

  update: async (id: string, data: any) => {
    const response = await api.patch(`/tasks/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    await api.delete(`/tasks/${id}`);
  },
};

// Allocations API
export const allocationsApi = {
  list: async (params?: any) => {
    const response = await api.get('/allocations', { params });
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get(`/allocations/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/allocations', data);
    return response.data;
  },

  update: async (id: string, data: any) => {
    const response = await api.patch(`/allocations/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    await api.delete(`/allocations/${id}`);
  },

  bulkUpsert: async (data: any) => {
    const response = await api.post('/allocations:bulk-upsert', data);
    return response.data;
  },
};

// Reports API
export const reportsApi = {
  utilization: async (params?: any) => {
    const response = await api.get('/reports/utilization', { params });
    return response.data;
  },

  overbookings: async (params?: any) => {
    const response = await api.get('/reports/overbookings', { params });
    return response.data;
  },

  capacityVsLoad: async (params?: any) => {
    const response = await api.get('/reports/capacity-vs-load', { params });
    return response.data;
  },

  exportAllocations: async (params?: any) => {
    const response = await api.get('/exports/allocations.csv', { 
      params,
      responseType: 'blob',
    });
    return response.data;
  },
};

// Calendars API
export const calendarsApi = {
  list: async (params?: any) => {
    const response = await api.get('/calendars', { params });
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get(`/calendars/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/calendars', data);
    return response.data;
  },

  update: async (id: string, data: any) => {
    const response = await api.patch(`/calendars/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    await api.delete(`/calendars/${id}`);
  },

  addHoliday: async (calendarId: string, data: any) => {
    const response = await api.post(`/calendars/${calendarId}/holidays`, data);
    return response.data;
  },

  removeHoliday: async (calendarId: string, holidayId: string) => {
    await api.delete(`/calendars/${calendarId}/holidays/${holidayId}`);
  },
};

export default api;
/**
 * API Client for Marketing2 Frontend
 * Axios instance with interceptors and API endpoint definitions
 */

import axios, { type AxiosInstance } from 'axios';

// Create axios instance with base configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available (future enhancement)
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors
    if (error.response) {
      switch (error.response.status) {
        case 401:
          console.error('Unauthorized access');
          break;
        case 403:
          console.error('Forbidden');
          break;
        case 404:
          console.error('Resource not found');
          break;
        case 500:
          console.error('Server error:', error.response.data?.detail);
          break;
        default:
          console.error('API error:', error.response.data);
      }
    } else if (error.request) {
      console.error('Network error: No response received');
    } else {
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// API Endpoints

/**
 * Workflow API
 */
export const workflowAPI = {
  /**
   * Create a new video generation workflow
   */
  create: (data: {
    novel_text: string;
    role_setting?: string;
    style?: string;
  }) => {
    return apiClient.post('/api/v1/workflow/create', data);
  },

  /**
   * Get workflow status by task_id
   */
  get: (taskId: string) => {
    return apiClient.get(`/api/v1/workflow/${taskId}`);
  },

  /**
   * Cancel a workflow
   */
  cancel: (taskId: string) => {
    return apiClient.post(`/api/v1/workflow/${taskId}/cancel`);
  },
};

/**
 * Health check
 */
export const healthAPI = {
  check: () => apiClient.get('/health'),
};

export default apiClient;

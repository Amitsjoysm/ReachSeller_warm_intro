import axios from 'axios';
import Constants from 'expo-constants';
import * as SecureStore from 'expo-secure-store';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';

console.log('API_URL configured as:', API_URL);
console.log('Full API baseURL:', `${API_URL}/api`);

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await SecureStore.getItemAsync('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Error getting token:', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle token expiration
      await SecureStore.deleteItemAsync('access_token');
      await SecureStore.deleteItemAsync('refresh_token');
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authAPI = {
  register: (data: any) => api.post('/auth/register', data),
  verifyEmail: (data: any) => api.post('/auth/verify-email', data),
  login: (data: any) => api.post('/auth/login', data),
  resendOTP: (data: any) => api.post('/auth/resend-otp', data),
  getMe: () => api.get('/auth/me'),
};

// LinkedIn API
export const linkedInAPI = {
  getAuthUrl: () => api.get('/linkedin/auth-url'),
  callback: (data: any) => api.post('/linkedin/callback', data),
  getMyMetrics: () => api.get('/linkedin/my-metrics'),
  reverify: () => api.post('/linkedin/reverify'),
};

// Services API
export const servicesAPI = {
  create: (data: any) => api.post('/services/create', data),
  search: (params: any) => api.get('/services/search', { params }),
  getById: (id: string) => api.get(`/services/${id}`),
  update: (id: string, data: any) => api.put(`/services/${id}`, data),
  delete: (id: string) => api.delete(`/services/${id}`),
  getMyServices: () => api.get('/services/seller/my-services'),
};

// Wallet API
export const walletAPI = {
  purchaseCredits: (data: any) => api.post('/wallet/purchase-credits', data),
  getBalance: () => api.get('/wallet/balance'),
  getTransactions: () => api.get('/wallet/transactions'),
  withdraw: (data: any) => api.post('/wallet/withdraw', data),
};

// Orders API
export const ordersAPI = {
  create: (data: any) => api.post('/orders/create', data),
  accept: (id: string) => api.post(`/orders/${id}/accept`),
  decline: (id: string, data: any) => api.post(`/orders/${id}/decline`, data),
  deliver: (id: string, data: any) => api.post(`/orders/${id}/deliver`, data),
  approve: (id: string) => api.post(`/orders/${id}/approve`),
  requestRevision: (id: string, data: any) => api.post(`/orders/${id}/request-revision`, data),
  getBuyerOrders: (params?: any) => api.get('/orders/buyer', { params }),
  getSellerOrders: (params?: any) => api.get('/orders/seller', { params }),
  getById: (id: string) => api.get(`/orders/${id}`),
};

// Reviews API
export const reviewsAPI = {
  create: (data: any) => api.post('/reviews/create', data),
  getUserReviews: (userId: string) => api.get(`/reviews/user/${userId}`),
  getMyReviews: () => api.get('/reviews/my-reviews'),
};

// Disputes API
export const disputesAPI = {
  create: (data: any) => api.post('/disputes/create', data),
  respond: (id: string, data: any) => api.post(`/disputes/${id}/respond`, data),
  getUserDisputes: () => api.get('/disputes/user'),
  getById: (id: string) => api.get(`/disputes/${id}`),
};

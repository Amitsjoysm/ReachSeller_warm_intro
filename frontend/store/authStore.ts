import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { authAPI } from '../services/api';

interface User {
  _id: string;
  email: string;
  full_name: string;
  role: 'seller' | 'buyer' | 'both';
  profile_picture?: string;
  email_verified: boolean;
  seller_profile?: any;
  buyer_profile?: any;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<any>;
  verifyEmail: (email: string, otp: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
  setError: (error: string | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    try {
      set({ isLoading: true, error: null });
      const response = await authAPI.login({ email, password });
      
      await SecureStore.setItemAsync('access_token', response.data.access_token);
      await SecureStore.setItemAsync('refresh_token', response.data.refresh_token);
      
      set({ 
        user: response.data.user, 
        isAuthenticated: true, 
        isLoading: false 
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Login failed';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  register: async (data: any) => {
    try {
      set({ isLoading: true, error: null });
      const response = await authAPI.register(data);
      set({ isLoading: false });
      return response.data;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Registration failed';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  verifyEmail: async (email: string, otp: string) => {
    try {
      set({ isLoading: true, error: null });
      const response = await authAPI.verifyEmail({ email, otp });
      
      await SecureStore.setItemAsync('access_token', response.data.access_token);
      await SecureStore.setItemAsync('refresh_token', response.data.refresh_token);
      
      set({ 
        user: response.data.user, 
        isAuthenticated: true, 
        isLoading: false 
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Verification failed';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    try {
      await SecureStore.deleteItemAsync('access_token');
      await SecureStore.deleteItemAsync('refresh_token');
      set({ user: null, isAuthenticated: false });
    } catch (error) {
      console.error('Logout error:', error);
    }
  },

  loadUser: async () => {
    try {
      const token = await SecureStore.getItemAsync('access_token');
      if (token) {
        const response = await authAPI.getMe();
        set({ 
          user: response.data.user, 
          isAuthenticated: true 
        });
      }
    } catch (error) {
      console.error('Load user error:', error);
      await SecureStore.deleteItemAsync('access_token');
      await SecureStore.deleteItemAsync('refresh_token');
      set({ user: null, isAuthenticated: false });
    }
  },

  setError: (error: string | null) => set({ error }),
}));

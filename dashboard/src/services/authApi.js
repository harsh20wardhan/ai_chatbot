import api from './api';

// API methods for authentication using the backend API endpoints
export const authApi = {
  // Register a new user
  register: async (email, password, name) => {
    try {
      const response = await api.post('/auth/register', {
        email,
        password,
        name
      });
      return response.data;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  },
  
  // Login user
  login: async (email, password) => {
    try {
      console.log('AuthAPI: Attempting login with email:', email);
      console.log('AuthAPI: Making request to:', api.defaults.baseURL + '/auth/login');
      
      const response = await api.post('/auth/login', {
        email,
        password
      });
      
      console.log('AuthAPI: Login successful:', response.status);
      return response.data;
    } catch (error) {
      console.error('AuthAPI: Login error:', error);
      console.error('AuthAPI: Error response:', error.response?.data);
      console.error('AuthAPI: Error status:', error.response?.status);
      console.error('AuthAPI: Error config:', error.config);
      throw error;
    }
  },
  
  // Logout user
  logout: async () => {
    try {
      const response = await api.post('/auth/logout');
      return response.data;
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  },
  
  // Get current user
  getCurrentUser: async () => {
    try {
      const response = await api.get('/auth/user');
      return response.data;
    } catch (error) {
      console.error('Get user error:', error);
      throw error;
    }
  }
};

export default authApi;
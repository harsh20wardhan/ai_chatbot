import React, { createContext, useState, useContext, useEffect } from 'react';
import { authApi } from '../services/authApi';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('auth_token') || null);

  // Check for existing session on mount
  useEffect(() => {
    async function getInitialSession() {
      try {
        setLoading(true);
        
        // If we have a token in localStorage, try to get the current user
        if (token) {
          try {
            const userData = await authApi.getCurrentUser();
            setUser(userData.user);
          } catch (err) {
            // If the token is invalid, clear it
            localStorage.removeItem('auth_token');
            setToken(null);
            setUser(null);
          }
        }
      } catch (error) {
        console.error('Error checking authentication:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    }

    getInitialSession();
  }, [token]);

  // Sign up function
  const signUp = async (email, password, name) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await authApi.register(email, password, name);
      
      if (response.token) {
        localStorage.setItem('auth_token', response.token);
        setToken(response.token);
        setUser(response.user);
      }
      
      return response;
    } catch (error) {
      console.error('Error signing up:', error);
      setError(error.response?.data?.message || error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Sign in function
  const signIn = async (email, password) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await authApi.login(email, password);
      
      if (response.token) {
        localStorage.setItem('auth_token', response.token);
        setToken(response.token);
        setUser(response.user);
      }
      
      return response;
    } catch (error) {
      console.error('Error signing in:', error);
      setError(error.response?.data?.message || error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Sign out function
  const signOut = async () => {
    try {
      setLoading(true);
      setError(null);
      
      await authApi.logout();
      
      localStorage.removeItem('auth_token');
      setToken(null);
      setUser(null);
    } catch (error) {
      console.error('Error signing out:', error);
      setError(error.response?.data?.message || error.message);
      
      // Even if the API call fails, we still want to clear the local session
      localStorage.removeItem('auth_token');
      setToken(null);
      setUser(null);
      
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // We'll implement these functions later when we have the API endpoints
  // Reset password function - placeholder for now
  const resetPassword = async (email) => {
    try {
      setLoading(true);
      setError(null);
      
      // This would be implemented when we have the API endpoint
      console.warn('Password reset not implemented in the API yet');
      
    } catch (error) {
      console.error('Error resetting password:', error);
      setError(error.response?.data?.message || error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Update password function - placeholder for now
  const updatePassword = async (newPassword) => {
    try {
      setLoading(true);
      setError(null);
      
      // This would be implemented when we have the API endpoint
      console.warn('Password update not implemented in the API yet');
      
    } catch (error) {
      console.error('Error updating password:', error);
      setError(error.response?.data?.message || error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const value = {
    user,
    token,
    loading,
    error,
    signUp,
    signIn,
    signOut,
    resetPassword,
    updatePassword,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
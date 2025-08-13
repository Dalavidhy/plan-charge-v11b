import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { authAPI } from "@/config/api";

interface User {
  id: string;
  email: string;
  full_name: string;
  org_id: string;
  roles?: string[];
}

interface AuthContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, firstName: string, lastName: string) => Promise<void>;
  logout: () => Promise<void>;
  userEmail?: string;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [userEmail, setUserEmail] = useState<string | undefined>(undefined);

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const userData = await authAPI.getCurrentUser();
          setUser(userData);
          setIsAuthenticated(true);
          setUserEmail(userData.email);
        } catch (error) {
          // Token invalid or expired
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      }
      setIsLoading(false);
    };
    
    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await authAPI.login(email, password);
      
      // Store tokens
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      
      // Set user data
      setUser(response.user);
      setIsAuthenticated(true);
      setUserEmail(email);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  };

  const register = async (email: string, password: string, firstName: string, lastName: string) => {
    try {
      await authAPI.register({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
      });
      
      // Auto-login after successful registration
      await login(email, password);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout API call failed:', error);
    } finally {
      setIsAuthenticated(false);
      setUser(null);
      setUserEmail(undefined);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  };

  const value = useMemo(
    () => ({ 
      isAuthenticated, 
      isLoading,
      user,
      login, 
      register,
      logout, 
      userEmail 
    }), 
    [isAuthenticated, isLoading, user, userEmail]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};

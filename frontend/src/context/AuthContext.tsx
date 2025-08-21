import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useMsal, useIsAuthenticated } from "@azure/msal-react";
import { authAPI } from "@/config/api";
import { logger } from "@/utils/logger";

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
  logout: () => Promise<void>;
  userEmail?: string;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { accounts, inProgress, instance } = useMsal();
  const msalIsAuthenticated = useIsAuthenticated();

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [userEmail, setUserEmail] = useState<string | undefined>(undefined);


  // Check if user is authenticated on mount and when MSAL state changes
  useEffect(() => {
    const checkAuth = async () => {
      logger.debug("🔍 AuthContext checkAuth() - inProgress:", inProgress, "msalAuth:", msalIsAuthenticated, "accounts:", accounts.length);

      // If MSAL is still in progress, wait
      if (inProgress !== "none") {
        logger.debug("⏳ AuthContext: MSAL in progress, waiting...");
        setIsLoading(true);
        return;
      }

      // If MSAL says not authenticated, don't check backend tokens
      if (!msalIsAuthenticated || accounts.length === 0) {
        logger.debug("🚫 AuthContext: MSAL not authenticated, clearing state");
        setIsAuthenticated(false);
        setUser(null);
        setUserEmail(undefined);
        setIsLoading(false);
        return;
      }

      // MSAL is authenticated, check if we have backend tokens
      const token = localStorage.getItem('access_token');
      logger.debug("🔍 AuthContext: Has backend token:", !!token);

      if (token) {
        try {
          logger.debug("🔍 AuthContext: Calling getCurrentUser() with token");
          const userData = await authAPI.getCurrentUser();
          logger.info("✅ AuthContext: getCurrentUser() success, setting authenticated state");
          setUser(userData);
          setIsAuthenticated(true);
          setUserEmail(userData.email);
        } catch (error: any) {
          logger.error("❌ AuthContext: getCurrentUser() failed:", error);
          // Only clear tokens for 401 (unauthorized), not for network/server errors
          if (error.response?.status === 401) {
            logger.info("🧹 AuthContext: Token invalid (401), clearing storage");
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            setIsAuthenticated(false);
            setUser(null);
          } else {
            logger.warn("⚠️ AuthContext: Network/server error, keeping tokens but showing as not authenticated");
            // For network errors, don't clear tokens but still show as not authenticated
            // This prevents constant clearing of valid tokens due to temporary network issues
            setIsAuthenticated(false);
            setUser(null);
          }
        }
      } else {
        // No backend token but MSAL is authenticated
        // This means we need to complete the token exchange
        logger.info("🔄 AuthContext: No backend token, but MSAL authenticated - need token exchange");
        setIsAuthenticated(false);
        setUser(null);
      }
      setIsLoading(false);
    };

    checkAuth();
  }, [msalIsAuthenticated, accounts, inProgress]);

  // Log authentication state changes
  useEffect(() => {
    logger.debug("🏁 AuthContext: Authentication state changed - isAuthenticated:", isAuthenticated, "isLoading:", isLoading);
  }, [isAuthenticated, isLoading]);

  const logout = async () => {
    try {
      // Try to call logout endpoint
      await authAPI.logout();
    } catch (error) {
      // Continue with logout even if API call fails
      logger.error('Logout API call failed:', error);
    } finally {
      // Clear everything locally
      setIsAuthenticated(false);
      setUser(null);
      setUserEmail(undefined);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');

      // Also logout from MSAL if available
      try {
        if (accounts.length > 0) {
          await instance.logoutRedirect({
            account: accounts[0],
            postLogoutRedirectUri: window.location.origin + '/login',
          });
        } else {
          window.location.href = '/login';
        }
      } catch (error) {
        logger.error('MSAL logout failed:', error);
        window.location.href = '/login';
      }
    }
  };

  const value = useMemo(
    () => ({
      isAuthenticated,
      isLoading,
      user,
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

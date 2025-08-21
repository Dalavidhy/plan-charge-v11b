/**
 * Custom hook for SSO authentication with Azure AD
 */

import { useState, useEffect, useCallback } from "react";
import { useMsal } from "@azure/msal-react";
import { InteractionStatus, AuthenticationResult, AccountInfo } from "@azure/msal-browser";
import { loginRequest, silentRequest } from "@/config/msalConfig";
import axios from "axios";
import { toast } from "sonner";
import { logger } from '@/utils/logger';

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface SSOStatus {
  enabled: boolean;
  configured: boolean;
  provider: string;
  login_url: string | null;
}

interface UseSSO {
  isAuthenticated: boolean;
  isLoading: boolean;
  account: AccountInfo | null;
  ssoStatus: SSOStatus | null;
  loginWithSSO: () => Promise<void>;
  logoutSSO: () => Promise<void>;
  exchangeCodeForToken: (code: string) => Promise<any>;
  checkSSOStatus: () => Promise<void>;
}

export const useSSO = (): UseSSO => {
  const { instance, accounts, inProgress } = useMsal();
  const [isLoading, setIsLoading] = useState(false);
  const [ssoStatus, setSSOStatus] = useState<SSOStatus | null>(null);
  
  const account = accounts[0] || null;
  const isAuthenticated = !!account;

  /**
   * Check if SSO is enabled and configured on the backend
   */
  const checkSSOStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/auth/sso/status`);
      setSSOStatus(response.data);
    } catch (error) {
      logger.error("Failed to check SSO status:", error);
      setSSOStatus({
        enabled: false,
        configured: false,
        provider: "Azure AD",
        login_url: null,
      });
    }
  }, []);

  /**
   * Login with Azure AD SSO
   */
  const loginWithSSO = useCallback(async () => {
    if (inProgress === InteractionStatus.None) {
      setIsLoading(true);
      try {
        // Use MSAL to initiate login
        const result: AuthenticationResult = await instance.loginPopup(loginRequest);
        
        if (result && result.account) {
          // Exchange the Azure AD token for our app tokens
          const response = await exchangeCodeForToken(result.accessToken);
          
          if (response) {
            toast.success("Connexion SSO réussie!");
            // The app will handle the tokens and redirect
          }
        }
      } catch (error) {
        logger.error("SSO login failed:", error);
        toast.error("Erreur lors de la connexion SSO");
      } finally {
        setIsLoading(false);
      }
    }
  }, [instance, inProgress]);

  /**
   * Exchange Azure AD authorization code for app tokens
   */
  const exchangeCodeForToken = useCallback(async (code: string): Promise<any> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/auth/sso/callback`, {
        code: code,
      });
      
      // Store tokens in localStorage
      if (response.data.access_token) {
        localStorage.setItem("access_token", response.data.access_token);
        localStorage.setItem("refresh_token", response.data.refresh_token);
        return response.data;
      }
    } catch (error) {
      logger.error("Failed to exchange code for token:", error);
      toast.error("Erreur lors de l'échange du code");
      throw error;
    }
  }, []);

  /**
   * Logout from SSO
   */
  const logoutSSO = useCallback(async () => {
    setIsLoading(true);
    try {
      // Get logout URL from backend
      const token = localStorage.getItem("access_token");
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/auth/sso/logout`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      
      // Clear local tokens
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      
      // Logout from MSAL
      await instance.logoutPopup({
        postLogoutRedirectUri: response.data.logout_url || window.location.origin,
      });
      
      toast.success("Déconnexion réussie");
    } catch (error) {
      logger.error("SSO logout failed:", error);
      // Still clear tokens even if logout fails
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      toast.error("Erreur lors de la déconnexion");
    } finally {
      setIsLoading(false);
    }
  }, [instance]);

  /**
   * Silent token acquisition
   */
  useEffect(() => {
    const acquireTokenSilent = async () => {
      if (account && inProgress === InteractionStatus.None) {
        try {
          const silentRequestWithAccount = {
            ...silentRequest,
            account: account,
          };
          await instance.acquireTokenSilent(silentRequestWithAccount);
        } catch (error) {
          logger.error("Silent token acquisition failed:", error);
        }
      }
    };

    acquireTokenSilent();
  }, [account, inProgress, instance]);

  /**
   * Check SSO status on mount
   */
  useEffect(() => {
    checkSSOStatus();
  }, [checkSSOStatus]);

  return {
    isAuthenticated,
    isLoading: isLoading || inProgress !== InteractionStatus.None,
    account,
    ssoStatus,
    loginWithSSO,
    logoutSSO,
    exchangeCodeForToken,
    checkSSOStatus,
  };
};
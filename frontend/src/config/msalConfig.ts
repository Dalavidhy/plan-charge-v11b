/**
 * MSAL configuration for Azure AD authentication
 */

import { Configuration, LogLevel } from "@azure/msal-browser";

// Get configuration from environment variables or use defaults
const AZURE_AD_CLIENT_ID = import.meta.env.VITE_AZURE_AD_CLIENT_ID || "";
const AZURE_AD_TENANT_ID = import.meta.env.VITE_AZURE_AD_TENANT_ID || "";
const AZURE_AD_REDIRECT_URI = import.meta.env.VITE_AZURE_AD_REDIRECT_URI || window.location.origin + "/auth/callback";


/**
 * MSAL configuration object for SPA with PKCE flow
 */
export const msalConfig: Configuration = {
  auth: {
    clientId: AZURE_AD_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${AZURE_AD_TENANT_ID}`,
    redirectUri: AZURE_AD_REDIRECT_URI,
    postLogoutRedirectUri: window.location.origin,
    navigateToLoginRequestUrl: false, // Handle redirects manually for better control
  },
  cache: {
    cacheLocation: "localStorage", // Store tokens in localStorage for persistence
    storeAuthStateInCookie: true, // Required for IE11/Edge support
  },
  system: {
    allowNativeBroker: false, // Disable native broker for web apps
    windowHashTimeout: 60000, // Increase timeout for slower connections
    iframeHashTimeout: 6000,
    loadFrameTimeout: 0,
    navigateFrameWait: 0,
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) {
          return;
        }
        switch (level) {
          case LogLevel.Error:
            console.error("MSAL Error:", message);
            return;
          case LogLevel.Info:
            console.info("MSAL Info:", message);
            return;
          case LogLevel.Verbose:
            console.debug("MSAL Verbose:", message);
            return;
          case LogLevel.Warning:
            console.warn("MSAL Warning:", message);
            return;
          default:
            return;
        }
      },
      logLevel: LogLevel.Info, // More verbose for debugging
    },
  },
};

/**
 * Scopes for initial login - includes all necessary permissions
 */
export const loginRequest = {
  scopes: [
    "openid",           // Required for OpenID Connect
    "profile",          // User profile information
    "email",            // Email address
    "User.Read",        // Read user profile
    "offline_access",   // Refresh tokens
  ],
  prompt: "select_account" as const, // Always show account picker
};

/**
 * Scopes for silent token acquisition
 */
export const silentRequest = {
  scopes: [
    "openid",
    "profile", 
    "email",
    "User.Read",
  ],
  forceRefresh: false,
};

/**
 * Graph API request configuration
 */
export const graphConfig = {
  graphMeEndpoint: "https://graph.microsoft.com/v1.0/me",
  scopes: ["User.Read"],
};

/**
 * Check if MSAL is properly configured
 */
export const isMSALConfigured = (): boolean => {
  return !!(AZURE_AD_CLIENT_ID && AZURE_AD_TENANT_ID);
};
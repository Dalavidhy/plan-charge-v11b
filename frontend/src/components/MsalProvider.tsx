/**
 * MSAL Provider wrapper component
 */

import React from "react";
import { MsalProvider as MSALProvider } from "@azure/msal-react";
import { PublicClientApplication } from "@azure/msal-browser";
import { msalConfig, isMSALConfigured } from "@/config/msalConfig";

// Create MSAL instance only if configured
const msalInstance = isMSALConfigured() 
  ? new PublicClientApplication(msalConfig)
  : null;

interface MsalProviderWrapperProps {
  children: React.ReactNode;
}

export const MsalProviderWrapper: React.FC<MsalProviderWrapperProps> = ({ children }) => {
  // If MSAL is not configured, just render children without provider
  if (!msalInstance) {
    return <>{children}</>;
  }

  return (
    <MSALProvider instance={msalInstance}>
      {children}
    </MSALProvider>
  );
};
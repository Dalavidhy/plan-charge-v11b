/**
 * Runtime configuration loader
 * Loads configuration from window.ENV_CONFIG (injected by entrypoint.sh)
 * Falls back to import.meta.env for development
 */
import { logger } from '@/utils/logger';

interface RuntimeConfig {
  VITE_AZURE_AD_CLIENT_ID: string;
  VITE_AZURE_AD_TENANT_ID: string;
  VITE_AZURE_AD_REDIRECT_URI: string;
  VITE_API_URL: string;
  VITE_GRYZZLY_USE_MOCK: string;
}

// Extend window interface to include our runtime config
declare global {
  interface Window {
    ENV_CONFIG?: RuntimeConfig;
  }
}

/**
 * Get configuration value with runtime override support
 */
function getConfigValue(key: keyof RuntimeConfig): string {
  // First try runtime config (production)
  if (window.ENV_CONFIG && window.ENV_CONFIG[key]) {
    return window.ENV_CONFIG[key];
  }

  // Fall back to build-time environment (development)
  const buildTimeValue = import.meta.env[key] as string;
  if (buildTimeValue) {
    return buildTimeValue;
  }

  // Handle specific defaults
  switch (key) {
    case 'VITE_API_URL':
      return '/api/v1';
    case 'VITE_GRYZZLY_USE_MOCK':
      return 'false';
    case 'VITE_AZURE_AD_REDIRECT_URI':
      return window.location.origin + '/auth/callback';
    default:
      return '';
  }
}

/**
 * Runtime configuration object
 */
export const runtimeConfig = {
  // Azure AD Configuration
  get azureClientId(): string {
    return getConfigValue('VITE_AZURE_AD_CLIENT_ID');
  },

  get azureTenantId(): string {
    return getConfigValue('VITE_AZURE_AD_TENANT_ID');
  },

  get azureRedirectUri(): string {
    return getConfigValue('VITE_AZURE_AD_REDIRECT_URI');
  },

  // API Configuration
  get apiUrl(): string {
    return getConfigValue('VITE_API_URL');
  },

  // Gryzzly Configuration
  get gryzzlyUseMock(): boolean {
    return getConfigValue('VITE_GRYZZLY_USE_MOCK') === 'true';
  },

  // Validation
  get isConfigured(): boolean {
    return !!(this.azureClientId && this.azureTenantId);
  },

  // Debug info
  get debugInfo(): Record<string, any> {
    return {
      source: window.ENV_CONFIG ? 'runtime' : 'build-time',
      azureClientId: this.azureClientId,
      azureTenantId: this.azureTenantId,
      azureRedirectUri: this.azureRedirectUri,
      apiUrl: this.apiUrl,
      gryzzlyUseMock: this.gryzzlyUseMock,
      isConfigured: this.isConfigured,
      windowConfig: !!window.ENV_CONFIG,
    };
  }
};

// Log configuration on load for debugging
logger.debug('🔧 Runtime Configuration Loaded:', runtimeConfig.debugInfo);

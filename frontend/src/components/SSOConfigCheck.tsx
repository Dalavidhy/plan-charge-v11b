import React from 'react';
import { runtimeConfig } from '@/config/runtimeConfig';

interface SSOConfigCheckProps {
  children: React.ReactNode;
}

const SSOConfigCheck: React.FC<SSOConfigCheckProps> = ({ children }) => {
  // Check if SSO is properly configured
  if (!runtimeConfig.isConfigured) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
              <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.872-.833-2.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Configuration requise
            </h2>
            
            <p className="text-sm text-gray-600 mb-6">
              L'authentification SSO n'est pas configurée correctement. 
              Veuillez contacter votre administrateur système.
            </p>
            
            <div className="bg-gray-50 rounded-md p-4 text-left">
              <h3 className="text-sm font-medium text-gray-900 mb-2">
                Pour l'administrateur :
              </h3>
              <ul className="text-xs text-gray-600 space-y-1">
                <li>• Configurez Azure AD dans le portail Azure</li>
                <li>• Ajoutez les variables d'environnement requises</li>
                <li>• Redémarrez l'application</li>
              </ul>
            </div>
            
            {/* Debug information (only in development) */}
            {import.meta.env.DEV && (
              <details className="mt-4 text-left">
                <summary className="text-xs text-gray-500 cursor-pointer">
                  Informations de débogage
                </summary>
                <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto">
                  {JSON.stringify(runtimeConfig.debugInfo, null, 2)}
                </pre>
              </details>
            )}
          </div>
        </div>
      </div>
    );
  }

  // SSO is configured, render children
  return <>{children}</>;
};

export default SSOConfigCheck;
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, XCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

interface DiagnosticResult {
  name: string;
  status: 'success' | 'error' | 'warning' | 'pending';
  message: string;
  details?: any;
}

export default function DiagnosticPanel() {
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<DiagnosticResult[]>([]);
  const { isAuthenticated, user } = useAuth();

  const runDiagnostic = async () => {
    setRunning(true);
    setResults([]);
    
    const newResults: DiagnosticResult[] = [];
    
    // Test 1: Authentication
    if (isAuthenticated && user) {
      newResults.push({
        name: 'Authentification',
        status: 'success',
        message: `Connecté en tant que ${user.email}`,
        details: { user: user }
      });
    } else {
      newResults.push({
        name: 'Authentification',
        status: 'error',
        message: 'Non authentifié',
        details: { isAuthenticated, user }
      });
    }
    
    // Test 2: API Configuration
    const apiUrl = import.meta.env.VITE_API_URL;
    if (apiUrl) {
      newResults.push({
        name: 'Configuration API',
        status: 'success',
        message: `API URL: ${apiUrl}`,
        details: { apiUrl }
      });
    } else {
      newResults.push({
        name: 'Configuration API',
        status: 'error',
        message: 'VITE_API_URL non configuré',
        details: { apiUrl }
      });
    }
    
    // Test 3: Backend Health
    try {
      const response = await fetch(`${apiUrl?.replace('/api/v1', '')}/health`);
      if (response.ok) {
        const data = await response.json();
        newResults.push({
          name: 'Backend Health',
          status: 'success',
          message: `Backend opérationnel (${data.status})`,
          details: data
        });
      } else {
        newResults.push({
          name: 'Backend Health',
          status: 'error',
          message: `Backend erreur HTTP ${response.status}`,
          details: { status: response.status, statusText: response.statusText }
        });
      }
    } catch (error) {
      newResults.push({
        name: 'Backend Health',
        status: 'error',
        message: 'Impossible de contacter le backend',
        details: error
      });
    }
    
    // Test 4: Token presence
    const token = localStorage.getItem('access_token');
    if (token) {
      // Try to decode token (basic check)
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp * 1000;
        const now = Date.now();
        
        if (exp > now) {
          newResults.push({
            name: 'Token JWT',
            status: 'success',
            message: `Token valide jusqu'à ${new Date(exp).toLocaleString()}`,
            details: { payload, expiresAt: new Date(exp) }
          });
        } else {
          newResults.push({
            name: 'Token JWT',
            status: 'error',
            message: 'Token expiré',
            details: { payload, expiresAt: new Date(exp) }
          });
        }
      } catch (error) {
        newResults.push({
          name: 'Token JWT',
          status: 'warning',
          message: 'Token présent mais illisible',
          details: { token: token.substring(0, 20) + '...', error }
        });
      }
    } else {
      newResults.push({
        name: 'Token JWT',
        status: 'error',
        message: 'Aucun token d\'accès trouvé',
        details: { token }
      });
    }

    // Test 5: Environment Variables
    const gryzzlyMock = import.meta.env.VITE_GRYZZLY_USE_MOCK;
    newResults.push({
      name: 'Variables d\'environnement',
      status: gryzzlyMock !== undefined ? 'success' : 'warning',
      message: `VITE_GRYZZLY_USE_MOCK=${gryzzlyMock}`,
      details: {
        VITE_API_URL: import.meta.env.VITE_API_URL,
        VITE_GRYZZLY_USE_MOCK: import.meta.env.VITE_GRYZZLY_USE_MOCK,
        VITE_AZURE_AD_TENANT_ID: import.meta.env.VITE_AZURE_AD_TENANT_ID
      }
    });
    
    setResults(newResults);
    setRunning(false);
  };

  const getStatusIcon = (status: DiagnosticResult['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Loader2 className="h-4 w-4 animate-spin" />;
    }
  };

  const getStatusVariant = (status: DiagnosticResult['status']) => {
    switch (status) {
      case 'success':
        return 'secondary' as const;
      case 'error':
        return 'destructive' as const;
      case 'warning':
        return 'outline' as const;
      default:
        return 'default' as const;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Diagnostic du système
          <Button 
            onClick={runDiagnostic} 
            disabled={running}
            size="sm"
          >
            {running ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                En cours...
              </>
            ) : (
              'Lancer le diagnostic'
            )}
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {results.length === 0 && !running && (
          <Alert>
            <AlertDescription>
              Cliquez sur "Lancer le diagnostic" pour vérifier la configuration du système.
            </AlertDescription>
          </Alert>
        )}
        
        {results.map((result, index) => (
          <div key={index} className="flex items-center justify-between p-3 border rounded">
            <div className="flex items-center gap-2">
              {getStatusIcon(result.status)}
              <span className="font-medium">{result.name}</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={getStatusVariant(result.status)}>
                {result.status}
              </Badge>
              <span className="text-sm text-muted-foreground max-w-md truncate">
                {result.message}
              </span>
            </div>
          </div>
        ))}
        
        {results.length > 0 && (
          <details className="mt-4">
            <summary className="cursor-pointer text-sm text-muted-foreground">
              Détails techniques (cliquer pour afficher)
            </summary>
            <pre className="mt-2 text-xs bg-muted p-3 rounded overflow-auto max-h-64">
              {JSON.stringify(results, null, 2)}
            </pre>
          </details>
        )}
      </CardContent>
    </Card>
  );
}
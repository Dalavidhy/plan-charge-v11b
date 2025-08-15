import { useEffect, useState } from "react";
import { setSEO } from "@/lib/seo";
import { Button } from "@/components/ui/button";
import { useNavigate, useLocation } from "react-router-dom";
import { useMsal, useIsAuthenticated } from "@azure/msal-react";
import { loginRequest, isMSALConfigured } from "@/config/msalConfig";
import { InteractionRequiredAuthError, AuthenticationResult } from "@azure/msal-browser";
import { api } from "@/config/api";
import { useAuth } from "@/context/AuthContext";

export default function Auth() {
  const navigate = useNavigate();
  const location = useLocation();
  const { instance, accounts, inProgress } = useMsal();
  const isAuthenticated = useIsAuthenticated();
  const { isAuthenticated: isBackendAuthenticated, isLoading: isAuthLoading } = useAuth();
  
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [hasProcessedAuth, setHasProcessedAuth] = useState(false);
  const [redirectCount, setRedirectCount] = useState(0);
  
  
  useEffect(() => {
    setSEO({
      title: "Connexion — Accès privé",
      description: "Accédez à la plateforme privée.",
      canonical: "/login",
    });
    
    // Reset redirect count when component mounts (user navigated back to login)
    setRedirectCount(0);
    console.log("🔄 Auth.tsx: Component mounted, reset redirect count");
  }, []);

  // Handle authentication state changes - but prevent multiple calls
  useEffect(() => {
    // Only process if we haven't already handled this state and we're not in the middle of processing
    if (isAuthenticated && accounts.length > 0 && !hasProcessedAuth && !isLoading) {
      // Additional check: only if we don't have backend tokens yet
      const existingToken = localStorage.getItem("access_token");
      if (!existingToken) {
        console.log("🔄 Auth.tsx: MSAL authenticated but no backend tokens, starting token exchange");
        handleAuthenticationSuccess();
      } else {
        console.log("✅ Auth.tsx: Already have backend tokens, marking as processed");
        setHasProcessedAuth(true); // Mark as processed to prevent further calls
      }
    }
  }, [isAuthenticated, accounts, hasProcessedAuth, isLoading]);

  // Redirect if already fully authenticated - with anti-loop protection
  useEffect(() => {
    console.log("🔀 Auth.tsx: Checking redirect - isAuthLoading:", isAuthLoading, "isBackendAuth:", isBackendAuthenticated, "redirectCount:", redirectCount);
    
    // Wait for auth context to fully load
    if (isAuthLoading) {
      console.log("⏳ Auth.tsx: AuthContext still loading, waiting...");
      return;
    }
    
    // Anti-loop protection: if we've tried to redirect too many times, stop
    if (redirectCount >= 3) {
      console.error("🚨 Auth.tsx: Too many redirect attempts, stopping to prevent infinite loop");
      setError("Problème de redirection détecté. Rechargez la page ou essayez de naviguer manuellement vers /plan");
      return;
    }
    
    // If user is fully authenticated via AuthContext, redirect to plan
    if (isBackendAuthenticated) {
      console.log("🚀 Auth.tsx: User authenticated via AuthContext, redirecting to /plan (attempt", redirectCount + 1, ")");
      setRedirectCount(prev => prev + 1);
      navigate("/plan", { replace: true });
      return;
    }
    
    console.log("🔍 Auth.tsx: User not yet authenticated, staying on login page");
  }, [isBackendAuthenticated, isAuthLoading, navigate, redirectCount]);

  // Note: MSAL React automatically handles redirects, no manual handling needed
  
  /**
   * Handle successful authentication by getting tokens and creating user in backend
   */
  const handleAuthenticationSuccess = async () => {
    if (isLoading || hasProcessedAuth) {
      console.log("🔄 Auth.tsx: handleAuthenticationSuccess() already in progress, skipping");
      return; // Prevent multiple simultaneous calls
    }
    
    console.log("🚀 Auth.tsx: Starting handleAuthenticationSuccess()");
    setIsLoading(true);
    setHasProcessedAuth(true); // Mark as processing to prevent duplicate calls
    setError("");
    
    try {
      // Check if we already have valid backend tokens
      const existingToken = localStorage.getItem("access_token");
      if (existingToken) {
        console.log("✅ Auth.tsx: User already has backend tokens, redirecting to /plan");
        navigate("/plan", { replace: true });
        return;
      }

      const account = accounts[0];
      if (!account) {
        throw new Error("No account found");
      }

      console.log("🔍 Auth.tsx: Getting access token for user:", account.username);
      // Get access token from MSAL
      const tokenResponse = await instance.acquireTokenSilent({
        ...loginRequest,
        account: account,
      });

      console.log("✅ Auth.tsx: MSAL token acquired, sending to backend");
      // Send Azure AD token to backend to create/update user
      const backendResponse = await api.post('/auth/sso/token-exchange', {
        azureToken: tokenResponse.accessToken,
        idToken: tokenResponse.idToken,
        userInfo: {
          email: account.username,
          name: account.name,
          id: account.localAccountId,
        }
      });

      console.log("✅ Auth.tsx: Backend token exchange successful");
      // Store backend tokens
      localStorage.setItem("access_token", backendResponse.data.access_token);
      localStorage.setItem("refresh_token", backendResponse.data.refresh_token);
      
      console.log("🚀 Auth.tsx: Tokens stored, navigating to /plan");
      // Navigate to main app
      navigate("/plan", { replace: true });
      
    } catch (error: any) {
      
      if (error instanceof InteractionRequiredAuthError) {
        // Token expired or requires interaction, trigger login
        setHasProcessedAuth(false); // Reset flag to allow retry
        await handleMSALLogin();
      } else if (error.response?.status === 429) {
        // Rate limiting error - wait before allowing retry
        setError("Trop de tentatives de connexion. Nouvelle tentative dans 10 secondes...");
        setTimeout(() => {
          setHasProcessedAuth(false); // Allow retry after delay
          setError(""); // Clear error message
        }, 10000); // Wait 10 seconds before retry
      } else if (error.response?.data?.detail?.includes("authorized domains")) {
        setError("Accès refusé. Seuls les utilisateurs @nda-partners.com sont autorisés.");
      } else if (error.response?.status >= 500) {
        setError("Erreur serveur temporaire. Veuillez réessayer dans quelques instants.");
        setHasProcessedAuth(false); // Allow retry for server errors
      } else {
        setError("Erreur lors de l'authentification. Veuillez réessayer.");
        setHasProcessedAuth(false); // Allow retry for other errors
      }
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Initiate MSAL login redirect
   */
  const handleMSALLogin = async () => {
    if (!isMSALConfigured()) {
      setError("Configuration Azure AD manquante. Contactez votre administrateur.");
      return;
    }

    setIsLoading(true);
    setError("");
    
    try {
      await instance.loginRedirect(loginRequest);
    } catch (error) {
      setError("Erreur lors de l'initialisation de la connexion");
      setIsLoading(false);
    }
  };

  // Show loading during MSAL operations or our processing
  if (isLoading || inProgress !== "none") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">
            {inProgress === "Login" ? "Redirection vers Microsoft..." : "Connexion en cours..."}
          </p>
        </div>
      </div>
    );
  }

  // If MSAL is not configured properly
  if (!isMSALConfigured()) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="max-w-md text-center">
          <h1 className="text-2xl font-bold mb-4">Configuration requise</h1>
          <p className="text-muted-foreground mb-4">
            L'authentification SSO n'est pas configurée correctement.
            Veuillez contacter votre administrateur système.
          </p>
          <div className="bg-muted p-4 rounded-lg text-left text-sm">
            <p className="font-semibold mb-2">Pour l'administrateur :</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Configurez Azure AD dans le portail Azure</li>
              <li>Ajoutez les variables d'environnement requises</li>
              <li>Redémarrez l'application</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }


  
  return (
    <div className="min-h-screen flex">
      <aside className="hidden md:flex w-1/2 items-center justify-center bg-hero animate-gradient">
        <div className="max-w-md mx-auto text-left text-primary-foreground p-8">
          <h1 className="text-3xl font-bold mb-4">Plan de Charge</h1>
          <p className="text-base/relaxed opacity-90">
            Plateforme de gestion RH sécurisée.
            Authentification via Microsoft Azure AD.
          </p>
        </div>
      </aside>
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-sm bg-card border rounded-xl shadow-sm p-6" style={{ boxShadow: "var(--shadow-glow)" }}>
          <h2 className="text-xl font-semibold mb-1">Connexion sécurisée</h2>
          <p className="text-sm text-muted-foreground mb-6">
            Utilisez votre compte Microsoft professionnel
          </p>
          
          {error && (
            <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-md mb-4">
              {error}
              {error.includes("redirection détecté") && (
                <div className="mt-3 space-y-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => navigate("/plan", { replace: true })}
                    className="w-full"
                  >
                    Aller directement au plan
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => window.location.reload()}
                    className="w-full"
                  >
                    Recharger la page
                  </Button>
                </div>
              )}
            </div>
          )}
          
          <Button
            className="w-full"
            size="lg"
            onClick={handleMSALLogin}
            disabled={isLoading || inProgress !== "none"}
          >
            <svg
              className="mr-2 h-5 w-5"
              viewBox="0 0 21 21"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <rect x="0.5" y="0.5" width="9" height="9" fill="#F25022" />
              <rect x="11.5" y="0.5" width="9" height="9" fill="#7FBA00" />
              <rect x="0.5" y="11.5" width="9" height="9" fill="#00A4EF" />
              <rect x="11.5" y="11.5" width="9" height="9" fill="#FFB900" />
            </svg>
            Se connecter avec Microsoft
          </Button>
          
          <p className="text-xs text-muted-foreground text-center mt-6">
            Seuls les utilisateurs @nda-partners.com sont autorisés.
          </p>
        </div>
      </main>
    </div>
  );
}
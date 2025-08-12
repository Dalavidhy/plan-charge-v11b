import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { AppStoreProvider } from "@/store/AppStore";
import Auth from "@/pages/Auth";
import PlanDeCharge from "@/pages/PlanDeCharge";
import DroitsTR from "@/pages/DroitsTR";
import Synchronisation from "@/pages/Synchronisation";
import Collaborateurs from "@/pages/Collaborateurs";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AuthProvider>
        <AppStoreProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<Auth />} />
              <Route path="/" element={<Navigate to="/plan" replace />} />
              <Route path="/plan" element={<ProtectedRoute><PlanDeCharge /></ProtectedRoute>} />
              <Route path="/droits-tr" element={<ProtectedRoute><DroitsTR /></ProtectedRoute>} />
              <Route path="/sync" element={<ProtectedRoute><Synchronisation /></ProtectedRoute>} />
              <Route path="/collaborateurs" element={<ProtectedRoute><Collaborateurs /></ProtectedRoute>} />
              {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </AppStoreProvider>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;

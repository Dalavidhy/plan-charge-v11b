import { useEffect, useState } from "react";
import { setSEO } from "@/lib/seo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/context/AuthContext";
import { useNavigate } from "react-router-dom";
export default function Auth() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@plancharge.fr");
  const [password, setPassword] = useState("Admin123!");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  useEffect(() => {
    setSEO({
      title: "Connexion — Accès privé",
      description: "Accédez à la plateforme privée.",
      canonical: "/login",
    });
  }, []);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    
    setError("");
    setIsLoading(true);
    
    try {
      await login(email, password);
      navigate("/plan", { replace: true });
    } catch (err: any) {
      setError(err.message || "Erreur de connexion");
    } finally {
      setIsLoading(false);
    }
  };
  return (
    <div className="min-h-screen flex">
      <aside className="hidden md:flex w-1/2 items-center justify-center bg-hero animate-gradient">
        <div className="max-w-md mx-auto text-left text-primary-foreground p-8">
          <h1 className="text-3xl font-bold mb-4">Plateforme RH</h1>
          <p className="text-base/relaxed opacity-90">
            Plan de charge, titres-restaurant, synchronisation Payfit & Gryzzly.
            Authentification factice (aucune donnée stockée côté serveur).
          </p>
        </div>
      </aside>
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-sm bg-card border rounded-xl shadow-sm p-6" style={{ boxShadow: "var(--shadow-glow)" }}>
          <h2 className="text-xl font-semibold mb-1">Connexion</h2>
          <p className="text-sm text-muted-foreground mb-6">Accès privé</p>
          <form onSubmit={onSubmit} className="space-y-4">
            {error && (
              <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-md">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <label className="text-sm font-medium">Email</label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="vous@entreprise.com" required disabled={isLoading} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Mot de passe</label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required disabled={isLoading} />
            </div>
            <Button className="w-full" type="submit" disabled={isLoading}>
              {isLoading ? "Connexion..." : "Se connecter"}
            </Button>
          </form>
        </div>
      </main>
    </div>
  );
}

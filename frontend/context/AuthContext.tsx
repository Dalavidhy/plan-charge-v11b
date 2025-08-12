import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

interface AuthContextValue {
  isAuthenticated: boolean;
  login: (email: string) => void;
  logout: () => void;
  userEmail?: string;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const STORAGE_KEY = "app:isAuthenticated";
const STORAGE_USER = "app:userEmail";

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userEmail, setUserEmail] = useState<string | undefined>(undefined);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    const email = localStorage.getItem(STORAGE_USER) || undefined;
    if (stored === "true") {
      setIsAuthenticated(true);
      setUserEmail(email);
    }
  }, []);

  const login = (email: string) => {
    setIsAuthenticated(true);
    setUserEmail(email);
    localStorage.setItem(STORAGE_KEY, "true");
    localStorage.setItem(STORAGE_USER, email);
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUserEmail(undefined);
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(STORAGE_USER);
  };

  const value = useMemo(() => ({ isAuthenticated, login, logout, userEmail }), [isAuthenticated, userEmail]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};

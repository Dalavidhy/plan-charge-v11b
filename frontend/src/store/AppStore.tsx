import React, { createContext, useContext, useEffect, useMemo, useReducer } from "react";
import { useAuth } from "@/context/AuthContext";
import collaboratorsService from "@/services/collaborators.service";
import { logger } from '@/utils/logger';

export type Collaborateur = {
  id: string;
  nom: string;
  email?: string;
  matricule?: string;
  department?: string;
  position?: string;
  eligibleTR: boolean;
  actif: boolean;
  source?: 'gryzzly' | 'payfit' | 'both';
  droitMensuel?: number; // nombre de tickets/mois
};

export type ConnectorKey = "payfit" | "gryzzly" | "titres";

type ConnectorState = {
  connected: boolean;
  lastSync?: string;
  logs: string[];
};

export type SyncRun = {
  id: string;
  connector: ConnectorKey | "global";
  startedAt: string;
  endedAt: string;
  status: "success" | "error";
  message?: string;
};

type PayfitUser = { id: string; nom: string; email: string; statut: "actif" | "inactif"; syncedAt?: string };
type PayfitContract = { id: string; intitulé: string; type: string; début?: string; fin?: string; syncedAt?: string };
type PayfitAbsence = { id: string; collaborateur: string; type: string; du: string; au: string; heures?: number; source?: string };
export type PayfitData = {
  counts: { users: number; contracts: number; absences: number };
  users: PayfitUser[];
  contracts: PayfitContract[];
  absences: PayfitAbsence[];
};

type GryUser = { id: string; nom: string; email: string; externalId?: string; syncedAt?: string };
type GryDeclaration = { id: string; collaborateur: string; date: string; projet: string; tache: string; heures: number; statut: string; syncedAt?: string };
type GryItem = { id: string; projet: string; tache: string; actif: boolean; syncedAt?: string };
export type GryzzlyData = {
  counts: { users: number; declarations: number; projects: number; tasks: number };
  users: GryUser[];
  declarations: GryDeclaration[];
  items: GryItem[]; // projets+tâches
};

type Forecasts = Record<string, Record<string, number>>; // collaborateurId -> { YYYY-MM: nombre }

type AppState = {
  collaborateurs: Collaborateur[];
  collaborateursLoading: boolean;
  collaborateursError: string | null;
  connectors: Record<ConnectorKey, ConnectorState>;
  forecasts: Forecasts;
  sync: { runs: SyncRun[] };
  payfit?: PayfitData;
  gryzzly?: GryzzlyData;
};

type Action =
  | { type: "TOGGLE_ELIGIBLE"; id: string }
  | { type: "TOGGLE_ACTIF"; id: string }
  | { type: "UPDATE_MATRICULE"; id: string; matricule: string }
  | { type: "SET_DROIT"; id: string; value?: number }
  | { type: "SET_FORECAST"; id: string; monthKey: string; value: number }
  | { type: "SET_CONNECTOR"; key: ConnectorKey; connected: boolean }
  | { type: "ADD_LOG"; key: ConnectorKey; message: string }
  | { type: "ADD_SYNC_RUN"; run: SyncRun }
  | { type: "SET_PAYFIT_DATA"; data: PayfitData }
  | { type: "SET_GRYZZLY_DATA"; data: GryzzlyData }
  | { type: "SET_COLLABORATEURS"; collaborateurs: Collaborateur[] }
  | { type: "SET_COLLABORATEURS_LOADING"; loading: boolean }
  | { type: "SET_COLLABORATEURS_ERROR"; error: string | null }
  | { type: "RESET" };

const STORAGE_KEY = "app:store";

// Start with empty collaborateurs - will be loaded from API
const initialCollaborateurs: Collaborateur[] = [];

const initialState: AppState = {
  collaborateurs: initialCollaborateurs,
  collaborateursLoading: false,
  collaborateursError: null,
  connectors: {
    payfit: { connected: false, logs: [] },
    gryzzly: { connected: false, logs: [] },
    titres: { connected: false, logs: [] },
  },
  forecasts: {},
  sync: {
    runs: [
      { id: "r1", connector: "payfit", startedAt: new Date(Date.now()-3600_000).toISOString(), endedAt: new Date(Date.now()-3400_000).toISOString(), status: "success", message: "Import utilisateurs (25)" },
      { id: "r2", connector: "gryzzly", startedAt: new Date(Date.now()-7200_000).toISOString(), endedAt: new Date(Date.now()-7000_000).toISOString(), status: "error", message: "API 502" },
      { id: "r3", connector: "global", startedAt: new Date(Date.now()-86400_000).toISOString(), endedAt: new Date(Date.now()-86300_000).toISOString(), status: "success", message: "Batch quotidien" },
    ],
  },
  payfit: {
    counts: { users: 25, contracts: 21, absences: 8 },
    users: [
      { id: "p1", nom: "Alice Martin", email: "alice@example.com", statut: "actif", syncedAt: new Date().toISOString() },
      { id: "p2", nom: "Hugo Bernard", email: "hugo@example.com", statut: "actif", syncedAt: new Date().toISOString() },
    ],
    contracts: [
      { id: "c1", intitulé: "CDI Développeuse", type: "CDI", début: "2022-03-01", syncedAt: new Date().toISOString() },
    ],
    absences: [
      { id: "a1", collaborateur: "Alice Martin", type: "CP", du: "2025-08-05", au: "2025-08-07", heures: 21, source: "Payfit" },
    ],
  },
  gryzzly: {
    counts: { users: 23, declarations: 340, projects: 12, tasks: 45 },
    users: [
      { id: "g1", nom: "Chloé Dupont", email: "chloe@example.com", externalId: "usr_123", syncedAt: new Date().toISOString() },
    ],
    declarations: [
      { id: "d1", collaborateur: "Chloé Dupont", date: "2025-08-11", projet: "Client A", tache: "Dev", heures: 7, statut: "synced", syncedAt: new Date().toISOString() },
    ],
    items: [
      { id: "i1", projet: "Client A", tache: "Dev", actif: true, syncedAt: new Date().toISOString() },
    ],
  },
};

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "TOGGLE_ELIGIBLE":
      return {
        ...state,
        collaborateurs: state.collaborateurs.map(c => c.id === action.id ? { ...c, eligibleTR: !c.eligibleTR } : c)
      };
    case "TOGGLE_ACTIF":
      return {
        ...state,
        collaborateurs: state.collaborateurs.map(c => c.id === action.id ? { ...c, actif: !c.actif } : c)
      };
    case "UPDATE_MATRICULE":
      return {
        ...state,
        collaborateurs: state.collaborateurs.map(c => c.id === action.id ? { ...c, matricule: action.matricule } : c)
      };
    case "SET_DROIT":
      return {
        ...state,
        collaborateurs: state.collaborateurs.map(c => c.id === action.id ? { ...c, droitMensuel: action.value } : c)
      };
    case "SET_FORECAST": {
      const forId = state.forecasts[action.id] ?? {};
      return {
        ...state,
        forecasts: {
          ...state.forecasts,
          [action.id]: { ...forId, [action.monthKey]: action.value },
        },
      };
    }
    case "SET_CONNECTOR": {
      return {
        ...state,
        connectors: {
          ...state.connectors,
          [action.key]: {
            ...(state.connectors[action.key] ?? { connected: false, logs: [] }),
            connected: action.connected,
            lastSync: action.connected ? new Date().toISOString() : state.connectors[action.key]?.lastSync,
          },
        },
      };
    }
    case "ADD_LOG": {
      const prev = state.connectors[action.key] ?? { connected: false, logs: [] };
      return {
        ...state,
        connectors: {
          ...state.connectors,
          [action.key]: {
            ...prev,
            logs: [`${new Date().toLocaleString()} – ${action.message}`, ...prev.logs].slice(0, 200),
          },
        },
      };
    }
    case "ADD_SYNC_RUN": {
      return {
        ...state,
        sync: { runs: [action.run, ...(state.sync?.runs ?? [])].slice(0, 500) },
      };
    }
    case "SET_PAYFIT_DATA": {
      return { ...state, payfit: action.data };
    }
    case "SET_GRYZZLY_DATA": {
      return { ...state, gryzzly: action.data };
    }
    case "SET_COLLABORATEURS": {
      return { ...state, collaborateurs: action.collaborateurs, collaborateursLoading: false, collaborateursError: null };
    }
    case "SET_COLLABORATEURS_LOADING": {
      return { ...state, collaborateursLoading: action.loading };
    }
    case "SET_COLLABORATEURS_ERROR": {
      return { ...state, collaborateursError: action.error, collaborateursLoading: false };
    }
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

const AppStoreContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<Action>;
} | undefined>(undefined);

export const AppStoreProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [state, dispatch] = useReducer(reducer, initialState, (init) => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) return JSON.parse(stored) as AppState;
    } catch {}
    return init;
  });

  // Auto-load collaborators when user becomes authenticated
  useEffect(() => {
    const loadCollaborators = async () => {
      // Only load if authenticated, not already loading, and no collaborators yet
      if (!isAuthenticated || isAuthLoading || state.collaborateursLoading || state.collaborateurs.length > 0) {
        return;
      }

      logger.debug("🔄 AppStore: Auto-loading collaborators");
      dispatch({ type: "SET_COLLABORATEURS_LOADING", loading: true });
      
      try {
        const collaborators = await collaboratorsService.getCollaborators();
        logger.debug("✅ AppStore: Loaded", collaborators.length, "collaborators");
        dispatch({ type: "SET_COLLABORATEURS", collaborateurs: collaborators });
      } catch (error) {
        logger.error("❌ AppStore: Failed to load collaborators:", error);
        dispatch({ type: "SET_COLLABORATEURS_ERROR", error: "Impossible de charger les collaborateurs" });
      }
    };

    loadCollaborators();
  }, [isAuthenticated, isAuthLoading, state.collaborateursLoading, state.collaborateurs.length]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  const value = useMemo(() => ({ state, dispatch }), [state]);

  return <AppStoreContext.Provider value={value}>{children}</AppStoreContext.Provider>;
};

export const useAppStore = () => {
  const ctx = useContext(AppStoreContext);
  if (!ctx) throw new Error("useAppStore must be used within AppStoreProvider");
  return ctx;
};

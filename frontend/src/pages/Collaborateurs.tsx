import { useEffect, useState } from "react";
import AppLayout from "@/layouts/AppLayout";
import { useAppStore } from "@/store/AppStore";
import { setSEO } from "@/lib/seo";
import collaboratorsService from "@/services/collaborators.service";
import { Loader2, AlertCircle, Download, RefreshCw } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";

export default function Collaborateurs() {
  const { state, dispatch } = useAppStore();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState<string | null>(null);
  const [showOnlyActive, setShowOnlyActive] = useState(() => {
    return localStorage.getItem('collaborateurs.showOnlyActive') === 'true';
  });

  useEffect(() => {
    setSEO({
      title: "Collaborateurs",
      description: "Gérer l'activité et l'éligibilité titres-restaurant.",
      canonical: "/collaborateurs",
    });
    loadCollaborators();
  }, []);

  const loadCollaborators = async () => {
    try {
      setLoading(true);
      setError(null);
      const collaborators = await collaboratorsService.getCollaborators();
      dispatch({ type: "SET_COLLABORATEURS", collaborateurs: collaborators });
    } catch (err) {
      console.error("Error loading collaborators:", err);
      setError("Erreur lors du chargement des collaborateurs");
      toast({
        title: "Erreur",
        description: "Impossible de charger les collaborateurs",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActif = async (id: string, currentStatus: boolean) => {
    try {
      setUpdating(id);
      await collaboratorsService.toggleActive(id, currentStatus);
      // Update local state
      dispatch({ type: 'TOGGLE_ACTIF', id });
      toast({
        title: "Succès",
        description: "Statut mis à jour",
      });
    } catch (err) {
      console.error("Error toggling active status:", err);
      toast({
        title: "Erreur",
        description: "Impossible de mettre à jour le statut",
        variant: "destructive",
      });
    } finally {
      setUpdating(null);
    }
  };

  const handleToggleEligible = async (id: string, currentStatus: boolean) => {
    try {
      setUpdating(id);
      await collaboratorsService.toggleEligible(id, currentStatus);
      // Update local state
      dispatch({ type: 'TOGGLE_ELIGIBLE', id });
      toast({
        title: "Succès",
        description: "Éligibilité TR mise à jour",
      });
    } catch (err) {
      console.error("Error toggling TR eligibility:", err);
      toast({
        title: "Erreur",
        description: "Impossible de mettre à jour l'éligibilité TR",
        variant: "destructive",
      });
    } finally {
      setUpdating(null);
    }
  };

  const handleExportCSV = () => {
    const date = new Date().toISOString().split('T')[0];
    const dataToExport = showOnlyActive 
      ? state.collaborateurs.filter(c => c.actif)
      : state.collaborateurs;
    collaboratorsService.downloadCSV(dataToExport, `collaborateurs_${date}.csv`);
    toast({
      title: "Export réussi",
      description: "Le fichier CSV a été téléchargé",
    });
  };

  // Filter collaborators based on active status
  const displayedCollaborateurs = showOnlyActive 
    ? state.collaborateurs.filter(c => c.actif)
    : state.collaborateurs;

  return (
    <AppLayout title="Collaborateurs">
      <div className="mb-4 flex justify-between items-center">
        <div className="flex gap-2 items-center">
          <button
            onClick={loadCollaborators}
            disabled={loading}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Rafraîchir
          </button>
          <button
            onClick={handleExportCSV}
            disabled={loading || displayedCollaborateurs.length === 0}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="h-4 w-4 mr-2" />
            Exporter CSV
          </button>
          <div className="ml-4 pl-4 border-l border-gray-300">
            <label className="inline-flex items-center">
              <input
                type="checkbox"
                checked={showOnlyActive}
                onChange={(e) => {
                  setShowOnlyActive(e.target.checked);
                  localStorage.setItem('collaborateurs.showOnlyActive', e.target.checked.toString());
                }}
                className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
              />
              <span className="ml-2 text-sm text-gray-700">Actifs uniquement</span>
            </label>
          </div>
        </div>
        <div className="text-sm text-muted-foreground">
          {displayedCollaborateurs.length} affiché{displayedCollaborateurs.length > 1 ? 's' : ''} / {state.collaborateurs.length} total • 
          {state.collaborateurs.filter(c => c.actif).length} actif{state.collaborateurs.filter(c => c.actif).length > 1 ? 's' : ''} • 
          {state.collaborateurs.filter(c => c.eligibleTR).length} éligible{state.collaborateurs.filter(c => c.eligibleTR).length > 1 ? 's' : ''} TR
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Chargement des collaborateurs...</span>
        </div>
      ) : error ? (
        <div className="flex items-center justify-center py-12">
          <AlertCircle className="h-8 w-8 text-destructive" />
          <span className="ml-2 text-destructive">{error}</span>
        </div>
      ) : (
        <div className="rounded-lg border shadow-sm overflow-hidden" style={{ boxShadow: "var(--shadow-elev)" }}>
          <table className="w-full text-sm">
            <thead className="bg-card">
              <tr>
                <th className="px-3 py-2 text-left">Matricule</th>
                <th className="px-3 py-2 text-left">Nom</th>
                <th className="px-3 py-2 text-left">Email</th>
                <th className="px-3 py-2 text-left">Département</th>
                <th className="px-3 py-2 text-center">Source</th>
                <th className="px-3 py-2 text-center">Actif</th>
                <th className="px-3 py-2 text-center">Éligible TR</th>
              </tr>
            </thead>
            <tbody>
              {displayedCollaborateurs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-muted-foreground">
                    {showOnlyActive && state.collaborateurs.length > 0 
                      ? "Aucun collaborateur actif trouvé" 
                      : "Aucun collaborateur trouvé"}
                  </td>
                </tr>
              ) : (
                displayedCollaborateurs.map((c) => (
                  <tr key={c.id} className="border-t hover:bg-gray-50">
                    <td className="px-3 py-2 text-muted-foreground">
                      {c.matricule || '-'}
                    </td>
                    <td className="px-3 py-2 font-medium">{c.nom}</td>
                    <td className="px-3 py-2 text-sm text-muted-foreground">
                      {c.email || '-'}
                    </td>
                    <td className="px-3 py-2 text-sm text-muted-foreground">
                      {c.department || '-'}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        c.source === 'both' ? 'bg-green-100 text-green-800' :
                        c.source === 'gryzzly' ? 'bg-blue-100 text-blue-800' :
                        'bg-purple-100 text-purple-800'
                      }`}>
                        {c.source === 'both' ? 'Les deux' : c.source?.charAt(0).toUpperCase() + c.source?.slice(1)}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-center">
                      <input 
                        type="checkbox" 
                        checked={c.actif} 
                        disabled={updating === c.id}
                        onChange={() => handleToggleActif(c.id, c.actif)}
                        className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      />
                    </td>
                    <td className="px-3 py-2 text-center">
                      <input 
                        type="checkbox" 
                        checked={c.eligibleTR} 
                        disabled={updating === c.id || !c.actif}
                        onChange={() => handleToggleEligible(c.id, c.eligibleTR)}
                        className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        title={!c.actif ? "Le collaborateur doit être actif pour être éligible TR" : ""}
                      />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
      
      <p className="text-xs text-muted-foreground mt-3">
        Les collaborateurs inactifs n'apparaissent pas dans le plan de charge. 
        L'éligibilité TR est basée sur les contrats actifs dans Payfit.
      </p>
    </AppLayout>
  );
}

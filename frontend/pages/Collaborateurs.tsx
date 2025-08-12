import { useEffect } from "react";
import AppLayout from "@/layouts/AppLayout";
import { useAppStore } from "@/store/AppStore";
import { setSEO } from "@/lib/seo";

export default function Collaborateurs() {
  const { state, dispatch } = useAppStore();

  useEffect(() => {
    setSEO({
      title: "Collaborateurs",
      description: "Gérer l’activité et l’éligibilité titres-restaurant.",
      canonical: "/collaborateurs",
    });
  }, []);

  return (
    <AppLayout title="Collaborateurs">
      <div className="rounded-lg border shadow-sm overflow-hidden" style={{ boxShadow: "var(--shadow-elev)" }}>
        <table className="w-full text-sm">
          <thead className="bg-card">
            <tr>
              <th className="px-3 py-2 text-left">Nom</th>
              <th className="px-3 py-2 text-center">Actif</th>
              <th className="px-3 py-2 text-center">Éligible TR</th>
            </tr>
          </thead>
          <tbody>
            {state.collaborateurs.map((c) => (
              <tr key={c.id} className="border-t">
                <td className="px-3 py-2 font-medium">{c.nom}</td>
                <td className="px-3 py-2 text-center">
                  <input type="checkbox" checked={c.actif} onChange={() => dispatch({ type: 'TOGGLE_ACTIF', id: c.id })} />
                </td>
                <td className="px-3 py-2 text-center">
                  <input type="checkbox" checked={c.eligibleTR} onChange={() => dispatch({ type: 'TOGGLE_ELIGIBLE', id: c.id })} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted-foreground mt-3">Les collaborateurs inactifs n’apparaissent pas dans le plan de charge.</p>
    </AppLayout>
  );
}

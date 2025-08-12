import { useEffect, useMemo, useState } from "react";
import Holidays from "date-holidays";
import { ChevronLeft, ChevronRight, ChevronDown } from "lucide-react";
import AppLayout from "@/layouts/AppLayout";
import { useAppStore } from "@/store/AppStore";
import { Button } from "@/components/ui/button";
import { setSEO } from "@/lib/seo";

function escapeCSV(val: string) {
  return '"' + val.replace(/"/g, '""') + '"';
}
function toCSV(rows: string[][]) {
  return rows.map(r => r.map((c) => escapeCSV(c ?? "")).join(',')).join('\n');
}

export default function DroitsTR() {
  const { state, dispatch } = useAppStore();

  const now = new Date();
  const [month, setMonth] = useState<string>(`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`);
  const { year, monthIndex } = useMemo(() => ({
    year: parseInt(month.split("-")[0]),
    monthIndex: parseInt(month.split("-")[1]) - 1,
  }), [month]);
  const days = useMemo(() => {
    const date = new Date(year, monthIndex, 1);
    const hd = new Holidays("FR");
    const holidays = (hd.getHolidays(year) || [])
      .filter(h => new Date(h.date).getMonth() === monthIndex)
      .map(h => new Date(h.date).getDate());
    const arr: { d: number; isWeekend: boolean; isHoliday: boolean }[] = [];
    while (date.getMonth() === monthIndex) {
      const d = date.getDate();
      const day = date.getDay();
      arr.push({ d, isWeekend: day === 0 || day === 6, isHoliday: holidays.includes(d) });
      date.setDate(d + 1);
    }
    return arr;
  }, [year, monthIndex]);
  const monthKey = `${year}-${String(monthIndex+1).padStart(2,'0')}`;
  const holidaysOnWeekdays = useMemo(() => days.filter(d => !d.isWeekend && d.isHoliday).length, [days]);
  const workingDays = useMemo(() => days.filter(d => !d.isWeekend && !d.isHoliday).length, [days]);

  const absencesFor = useMemo(() => {
    const map: Record<string, { date: string; type: string; jours: number }[]> = {};
    state.collaborateurs.forEach((c) => {
      const arr: { date: string; type: string; jours: number }[] = [];
      days.forEach((day) => {
        if (!day.isWeekend && !day.isHoliday) {
          if (day.d % 11 === 0) arr.push({ date: `${year}-${String(monthIndex+1).padStart(2,'0')}-${String(day.d).padStart(2,'0')}`, type: "RTT", jours: 1 });
          else if (day.d % 13 === 0) arr.push({ date: `${year}-${String(monthIndex+1).padStart(2,'0')}-${String(day.d).padStart(2,'0')}`, type: "Congés", jours: 1 });
        }
      });
      map[c.id] = arr;
    });
    return map;
  }, [state.collaborateurs, days, monthKey]);

  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setSEO({
      title: `Droits Titres-Restaurant – ${monthKey}`,
      description: "Définir les droits TR par collaborateur et exporter en CSV.",
      canonical: "/droits-tr",
    });
  }, [monthKey]);

  const exportCSV = () => {
    const headers = ["Nom", "Actif", "Éligible TR", "Droit mensuel (tickets)"];
    const rows = state.collaborateurs.map((c) => [
      c.nom,
      c.actif ? "Oui" : "Non",
      c.eligibleTR ? "Oui" : "Non",
      String(c.droitMensuel ?? ""),
    ]);
    const csv = toCSV([headers, ...rows]);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `droits-tr.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <AppLayout title="Droits Titres-Restaurant">
      <section className="space-y-4">
        <div className="flex flex-col gap-2">
          <div>
            <h2 className="text-xl font-semibold">Barème mensuel</h2>
            <p className="text-sm text-muted-foreground">Ajustez le droit mensuel (mock)</p>
          </div>
          <div className="flex items-center justify-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="icon"
              aria-label="Mois précédent"
              onClick={() => {
                const [y, m] = month.split("-").map(Number);
                const d = new Date(y, m - 2, 1);
                setMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
              }}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <input
              type="month"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              className="border bg-background rounded-md px-3 py-2"
              aria-label="Sélection du mois"
            />
            <Button
              type="button"
              variant="outline"
              size="icon"
              aria-label="Mois suivant"
              onClick={() => {
                const [y, m] = month.split("-").map(Number);
                const d = new Date(y, m, 1);
                setMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
              }}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
          <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">Jours ouvrés: {workingDays}</div>
            <div className="flex items-center gap-3">
              <div className="text-sm text-muted-foreground">Jours fériés (ouvrés): {holidaysOnWeekdays}</div>
              <Button onClick={exportCSV}>Exporter CSV</Button>
            </div>
          </div>
        </div>

        <div className="rounded-lg border shadow-sm overflow-hidden" style={{ boxShadow: "var(--shadow-elev)" }}>
          <table className="w-full text-sm">
            <thead className="bg-card">
              <tr>
                <th className="px-3 py-2 text-left">Nom</th>
                <th className="px-3 py-2 text-center">Actif</th>
                <th className="px-3 py-2 text-center">Éligible TR</th>
                <th className="px-3 py-2 text-right">Droit mensuel</th>
              </tr>
            </thead>
            <tbody>
              {state.collaborateurs.map((c) => (
                <>
                  <tr key={c.id} className="border-t">
                    <td className="px-3 py-2 font-medium">
                      <button
                        type="button"
                        aria-expanded={!!expanded[c.id]}
                        onClick={() => setExpanded((prev) => ({ ...prev, [c.id]: !prev[c.id] }))}
                        className="inline-flex items-center justify-center rounded-md border bg-background hover:bg-accent hover:text-accent-foreground mr-2 h-6 w-6"
                        title={expanded[c.id] ? "Réduire" : "Détails"}
                      >
                        {expanded[c.id] ? (
                          <ChevronDown className="w-4 h-4" />
                        ) : (
                          <ChevronRight className="w-4 h-4" />
                        )}
                      </button>
                      <span>{c.nom}</span>
                    </td>
                    <td className="px-3 py-2 text-center">{c.actif ? "Oui" : "Non"}</td>
                    <td className="px-3 py-2 text-center">{c.eligibleTR ? "Oui" : "Non"}</td>
                    <td className="px-3 py-2 text-right">
                      <input
                        type="number"
                        min={0}
                        value={c.droitMensuel ?? 0}
                        onChange={(e) => dispatch({ type: 'SET_DROIT', id: c.id, value: Number(e.target.value) })}
                        className="w-28 border bg-background rounded-md px-2 py-1 text-right"
                      />
                    </td>
                  </tr>
                  {expanded[c.id] && (
                    <tr key={`${c.id}-details`} className="border-t">
                      <td className="px-3 py-2 text-sm text-muted-foreground pl-8" colSpan={4}>
                        <div className="mb-1 font-medium">Détail du calcul</div>
                        <div className="mb-2">
                          {(() => {
                            const absDays = (absencesFor[c.id] || []).reduce((s, a) => s + (a.jours || 0), 0);
                            const theorique = Math.max(workingDays - absDays, 0);
                            return (
                              <span>
                                Jours ouvrés: {workingDays} − Absences: {absDays} = Droit théorique: {theorique}
                              </span>
                            );
                          })()}
                        </div>
                        <div className="mb-1 font-medium">Absences Payfit du mois</div>
                        <ul className="space-y-1">
                          {(absencesFor[c.id] || []).length > 0 ? (
                            absencesFor[c.id].map((a, idx) => (
                              <li key={idx} className="flex items-center justify-between">
                                <span>{a.date}</span>
                                <span className="text-muted-foreground">{a.type} — {a.jours}j</span>
                              </li>
                            ))
                          ) : (
                            <li className="text-muted-foreground">Aucune absence ce mois</li>
                          )}
                        </ul>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </AppLayout>
  );
}

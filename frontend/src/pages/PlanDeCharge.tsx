import { useEffect, useMemo, useState } from "react";
import Holidays from "date-holidays";
import AppLayout from "@/layouts/AppLayout";
import { useAppStore } from "@/store/AppStore";
import { setSEO } from "@/lib/seo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ChevronDown, ChevronRight, ChevronLeft, Plus, Loader2 } from "lucide-react";
import planChargeService, { PlanChargeData, PlanChargeCollaborator } from "@/services/plancharge.service";
import { useToast } from "@/hooks/use-toast";

function getDaysInMonth(year: number, monthIndex: number) {
  const date = new Date(year, monthIndex, 1);
  const days: { d: number; date: Date; isWeekend: boolean; isHoliday: boolean; label: string }[] = [];
  const hd = new Holidays("FR");
  // Collect holiday dates for the given month
  const holidays = (hd.getHolidays(year) || []).filter(h => {
    const d = new Date(h.date);
    return d.getMonth() === monthIndex;
  }).map(h => new Date(h.date).getDate());

  while (date.getMonth() === monthIndex) {
    const d = date.getDate();
    const day = date.getDay();
    const isWeekend = day === 0 || day === 6;
    const isHoliday = holidays.includes(d);
    const label = ["Dim","Lun","Mar","Mer","Jeu","Ven","Sam"][day];
    days.push({ d, date: new Date(date), isWeekend, isHoliday, label });
    date.setDate(d + 1);
  }
  return days;
}

export default function PlanDeCharge() {
  const { state, dispatch } = useAppStore();
  const { toast } = useToast();
  const now = new Date();
  const [month, setMonth] = useState<string>(`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`);
  const [loading, setLoading] = useState(false);
  const [planChargeData, setPlanChargeData] = useState<PlanChargeData | null>(null);

  const { year, monthIndex } = useMemo(() => ({
    year: parseInt(month.split("-")[0]),
    monthIndex: parseInt(month.split("-")[1]) - 1,
  }), [month]);

  const days = useMemo(() => getDaysInMonth(year, monthIndex), [year, monthIndex]);
  const monthKey = `${year}-${String(monthIndex+1).padStart(2,'0')}`;
  const actifs = state.collaborateurs.filter(c => c.actif);

  // Gestion de l'ouverture/fermeture des lignes détaillées
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  // Prévisionnel détaillé par jour (mock local) : idCollaborateur -> { YYYY-MM-DD: jours }
  const [dailyForecasts, setDailyForecasts] = useState<Record<string, Record<string, number>>>({});

  const dateKey = (d: number) => `${year}-${String(monthIndex+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
  const getDaily = (id: string, d: number) => dailyForecasts[id]?.[dateKey(d)] ?? 0;
  const setDaily = (id: string, d: number, value: number) => {
    setDailyForecasts((prev) => {
      const date = dateKey(d);
      const inner = { ...(prev[id] || {}) } as Record<string, number>;
      if (value > 0) inner[date] = value; else delete inner[date];
      const next = { ...prev, [id]: inner } as typeof prev;
      // Met à jour le total mensuel existant dans le store
      const prefix = `${year}-${String(monthIndex+1).padStart(2,'0')}-`;
      const sum = Object.entries(inner)
        .filter(([key]) => key.startsWith(prefix))
        .reduce((acc, [, v]) => acc + (v || 0), 0);
      dispatch({ type: 'SET_FORECAST', id, monthKey, value: Number(sum.toFixed(2)) });
      return next;
    });
  };

  // Prévisionnel par entrée (projet+tâche) stocké localement
  const [forecastEntries, setForecastEntries] = useState<Record<string, Record<string, { project: string; task: string; hours: number }[]>>>({});

  // Dialogs state
  const [addOpen, setAddOpen] = useState(false);
  const [addUser, setAddUser] = useState<string | null>(null);
  const [addProject, setAddProject] = useState<string>("");
  const [addTask, setAddTask] = useState<string>("");
  const [editTarget, setEditTarget] = useState<{ userId: string; date: string; index: number } | null>(null);

  const recomputeMonthly = (userId: string) => {
    const prefix = `${year}-${String(monthIndex+1).padStart(2,'0')}-`;
    const sumHours = Object.entries(forecastEntries[userId] || {})
      .filter(([d]) => d.startsWith(prefix))
      .reduce((acc, [, arr]) => acc + arr.reduce((s, e) => s + (e.hours || 0), 0), 0);
    dispatch({ type: 'SET_FORECAST', id: userId, monthKey, value: Number((sumHours / 7).toFixed(2)) });
  };

  const addForecastRange = (userId: string, project: string, task: string, startStr: string, endStr: string) => {
    const start = new Date(startStr);
    const end = new Date(endStr);
    if (isNaN(start.getTime()) || isNaN(end.getTime()) || start > end) return;
    const next = { ...(forecastEntries[userId] || {}) } as Record<string, {project:string; task:string; hours:number}[]>;
    const inMonth = (d: Date) => d.getFullYear() === year && d.getMonth() === monthIndex;
    const isOff = (d: Date) => {
      const meta = days.find(x => x.d === d.getDate());
      return !meta || meta.isWeekend || meta.isHoliday;
    };
    const cursor = new Date(start);
    while (cursor <= end) {
      if (inMonth(cursor) && !isOff(cursor)) {
        const dk = `${year}-${String(monthIndex+1).padStart(2,'0')}-${String(cursor.getDate()).padStart(2,'0')}`;
        const list = next[dk] ? [...next[dk]] : [];
        list.push({ project, task, hours: 7 });
        next[dk] = list;
      }
      cursor.setDate(cursor.getDate() + 1);
    }
    setForecastEntries(prev => ({ ...prev, [userId]: next }));
    setTimeout(() => recomputeMonthly(userId), 0);
  };

  const updateForecastEntry = (userId: string, date: string, index: number, hours: number) => {
    setForecastEntries(prev => {
      const userMap = { ...(prev[userId] || {}) };
      const list = userMap[date] ? [...userMap[date]] : [];
      if (list[index]) {
        list[index] = { ...list[index], hours };
        userMap[date] = list;
      }
      return { ...prev, [userId]: userMap };
    });
    setTimeout(() => recomputeMonthly(userId), 0);
  };

  const deleteForecastEntry = (userId: string, date: string, index: number) => {
    setForecastEntries(prev => {
      const userMap = { ...(prev[userId] || {}) };
      const list = userMap[date] ? [...userMap[date]] : [];
      list.splice(index, 1);
      if (list.length > 0) userMap[date] = list; else delete userMap[date];
      return { ...prev, [userId]: userMap };
    });
    setTimeout(() => recomputeMonthly(userId), 0);
  };

  // Fetch real data from backend
  const fetchPlanChargeData = async () => {
    setLoading(true);
    try {
      const data = await planChargeService.getPlanCharge(year, monthIndex + 1);
      setPlanChargeData(data);
    } catch (error) {
      console.error('Error fetching plan de charge:', error);
      toast({
        title: "Erreur",
        description: "Impossible de charger les données du plan de charge",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // Fetch data when month changes
  useEffect(() => {
    fetchPlanChargeData();
  }, [year, monthIndex]);

  useEffect(() => {
    setSEO({
      title: `Plan de charge – ${monthKey}`,
      description: "Vue mensuelle des collaborateurs avec weekends et jours fériés (FR).",
      canonical: "/plan",
    });
  }, [monthKey]);

  return (
    <AppLayout title="Plan de charge">
      <section className="space-y-4">
        <div className="flex flex-col gap-2">
          <div>
            <h2 className="text-xl font-semibold">Mois</h2>
            <p className="text-sm text-muted-foreground">Week-ends et jours fériés sont grisés automatiquement</p>
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
        </div>

        <div className="rounded-lg border shadow-sm overflow-x-auto" style={{ boxShadow: "var(--shadow-elev)" }}>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              <span className="ml-2 text-muted-foreground">Chargement du plan de charge...</span>
            </div>
          ) : (
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-card z-10">
              <tr>
                <th className="px-3 py-2 text-left w-56">Collaborateur</th>
                {days.map((day) => (
                  <th key={day.d} className={`px-2 py-2 text-center font-medium ${day.isWeekend || day.isHoliday ? 'text-muted-foreground' : ''}`}>
                    <div className="flex flex-col items-center">
                      <span>{day.label}</span>
                      <span className="tabular-nums">{day.d}</span>
                    </div>
                  </th>
                ))}
                <th className="px-3 py-2 text-right w-48">Prévisionnel (jours)</th>
              </tr>
            </thead>
            <tbody>
              {actifs.map((c) => {
                // Find matching collaborator in plan charge data
                const planChargeCollab = planChargeData?.collaborators.find(
                  pc => pc.email.toLowerCase() === c.email.toLowerCase()
                );
                const forecast = state.forecasts[c.id]?.[monthKey] ?? 0;
                return (
                  <>
                    <tr key={`${c.id}-main`} className="border-t">
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
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="ml-2"
                          onClick={() => { setAddUser(c.id); setAddProject(""); setAddTask(""); setAddOpen(true); }}
                          aria-label="Ajouter un prévisionnel"
                          title="Ajouter un prévisionnel"
                        >
                          <Plus className="w-4 h-4" />
                        </Button>
                      </td>
                      {days.map((day) => {
                        const dk = dateKey(day.d);
                        const declarations = planChargeCollab?.declarations?.[dk] || [];
                        const dayHours = planChargeService.calculateDayHours(
                          declarations,
                          planChargeCollab?.absences || [],
                          dk
                        );
                        
                        // Determine what to show: 
                        // - If weekend/holiday: nothing
                        // - If absence: show 0 (will be shown in detail)
                        // - If has declarations: show total hours
                        // - Otherwise: show standard 7h
                        let displayValue = null;
                        if (!day.isWeekend && !day.isHoliday) {
                          if (dayHours.hasAbsence) {
                            displayValue = 0; // Absence will be shown in detail rows
                          } else if (dayHours.totalProjectHours > 0) {
                            displayValue = dayHours.totalProjectHours;
                          } else {
                            displayValue = 7; // Standard working hours
                          }
                        }
                        
                        return (
                          <td key={`${c.id}-${day.d}`} className={`h-8 text-center ${day.isWeekend || day.isHoliday ? 'bg-muted' : ''}`}>
                            {displayValue !== null ? (
                              <span className={`mx-auto inline-flex items-center justify-center rounded-sm px-1.5 py-0.5 text-xs tabular-nums ${
                                dayHours.hasAbsence ? 'bg-orange-100 text-orange-800' : 
                                dayHours.totalProjectHours > 0 ? 'bg-blue-100 text-blue-800' : 
                                'bg-muted text-muted-foreground'
                              }`}>
                                {displayValue}
                              </span>
                            ) : null}
                          </td>
                        )
                      })}
                      <td className="px-3 py-2 text-right">
                        <input
                          type="number"
                          min={0}
                          value={forecast}
                          onChange={(e) => dispatch({ type: 'SET_FORECAST', id: c.id, monthKey, value: Number(e.target.value) })}
                          className="w-24 border bg-background rounded-md px-2 py-1 text-right"
                        />
                      </td>
                    </tr>
                    {expanded[c.id] && (() => {
                      // Build detail lines: Absences + Projects (imputations + prévisionnels)
                      const lines: { label: string; kind: 'absence' | 'imputation' | 'forecast'; hoursByDay: Record<string, number> }[] = [];

                      // Process Payfit absences
                      const absMap: Record<string, number> = {};
                      if (planChargeCollab?.absences) {
                        days.forEach(day => {
                          if (!day.isWeekend && !day.isHoliday) {
                            const dk = dateKey(day.d);
                            const absenceType = planChargeService.getAbsenceTypeForDate(dk, planChargeCollab.absences);
                            if (absenceType) {
                              absMap[dk] = 7; // Standard day for absence
                            }
                          }
                        });
                      }
                      if (Object.keys(absMap).length) {
                        lines.push({ label: 'Absences (Payfit)', kind: 'absence', hoursByDay: absMap });
                      }

                      // Process Gryzzly imputations grouped by project
                      const imputationsByProject: Record<string, Record<string, number>> = {};
                      if (planChargeCollab?.declarations) {
                        Object.entries(planChargeCollab.declarations).forEach(([date, decls]) => {
                          decls.forEach(decl => {
                            const projectName = decl.project_name;
                            if (!imputationsByProject[projectName]) {
                              imputationsByProject[projectName] = {};
                            }
                            imputationsByProject[projectName][date] = 
                              (imputationsByProject[projectName][date] || 0) + decl.hours;
                          });
                        });
                      }
                      const imputationLines = Object.entries(imputationsByProject).map(([label, hoursByDay]) => ({
                        label,
                        kind: 'imputation' as const,
                        hoursByDay,
                      }));

                      // Prévisionnels groupés par projet – tâche
                      const forecastsByLabel: Record<string, Record<string, number>> = {};
                      Object.entries(forecastEntries[c.id] || {}).forEach(([date, list]) => {
                        list.forEach((f) => {
                          const label = `${f.project} – ${f.task}`;
                          if (!forecastsByLabel[label]) forecastsByLabel[label] = {};
                          forecastsByLabel[label][date] = (forecastsByLabel[label][date] || 0) + f.hours;
                        });
                      });
                      const forecastLines = Object.entries(forecastsByLabel).map(([label, hoursByDay]) => ({
                        label,
                        kind: 'forecast' as const,
                        hoursByDay,
                      }));

                      // Sélectionne jusqu'à 4 lignes: Absences (si présente) + 3 projets max
                      const projectLines = [...imputationLines, ...forecastLines].slice(0, 3);
                      const finalLines = [
                        ...lines, // Absences en premier si existe
                        ...projectLines,
                      ];

                      return (
                        <>
                          {finalLines.map((line, li) => (
                            <tr key={`${c.id}-line-${li}`} className="border-t">
                              <td className="px-3 py-1">
                                <div className="pl-8 text-xs font-medium">{line.label}</div>
                              </td>
                              {days.map((day) => {
                                const dk = `${year}-${String(monthIndex + 1).padStart(2, '0')}-${String(day.d).padStart(2, '0')}`;
                                const hours = line.hoursByDay[dk] || 0;
                                const baseCell = `h-8 text-center ${day.isWeekend || day.isHoliday ? 'bg-muted' : ''}`;
                                const color =
                                  !day.isWeekend && !day.isHoliday && hours > 0
                                    ? line.kind === 'absence'
                                      ? 'bg-muted text-foreground'
                                      : 'bg-primary/10 text-foreground'
                                    : '';
                                const content = hours > 0 ? (
                                  <span className="mx-auto inline-flex items-center justify-center rounded-sm px-1.5 py-0.5 text-xs tabular-nums">
                                    {hours}
                                  </span>
                                ) : null;

                                // Pour les prévisionnels, clic pour éditer
                                const isEditable = line.kind === 'forecast' && !day.isWeekend && !day.isHoliday && hours > 0;
                                if (isEditable) {
                                  const dateList = forecastEntries[c.id]?.[dk] || [];
                                  const idx = dateList.findIndex((f) => `${f.project} – ${f.task}` === line.label);
                                  return (
                                    <td
                                      key={`${c.id}-line-${li}-${day.d}`}
                                      className={`${baseCell} ${color} cursor-pointer`}
                                      onClick={() => {
                                        if (idx >= 0) setEditTarget({ userId: c.id, date: dk, index: idx });
                                      }}
                                      title="Modifier le prévisionnel"
                                    >
                                      {content}
                                    </td>
                                  );
                                }
                                return (
                                  <td key={`${c.id}-line-${li}-${day.d}`} className={`${baseCell} ${color}`}>
                                    {content}
                                  </td>
                                );
                              })}
                              <td />
                            </tr>
                          ))}
                        </>
                      );
                    })()}

                  </>
                );
              })}
            </tbody>
          </table>
          )}
        </div>
        {/* Dialogs */}
        <Dialog open={addOpen} onOpenChange={setAddOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Ajouter un prévisionnel</DialogTitle>
            </DialogHeader>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const fd = new FormData(e.currentTarget);
                const start = String(fd.get('start') || '');
                const end = String(fd.get('end') || '');
                const project = addProject;
                const task = addTask;
                if (addUser && project && task && start && end) {
                  addForecastRange(addUser, project, task, start, end);
                  setAddOpen(false);
                  setAddProject("");
                  setAddTask("");
                }
              }}
              className="space-y-3"
            >
              <div className="grid gap-3">
                <div className="grid gap-1">
                  <Label htmlFor="project">Projet</Label>
                  <Select value={addProject} onValueChange={setAddProject}>
                    <SelectTrigger id="project" aria-label="Projet">
                      <SelectValue placeholder="Sélectionner un projet" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Projet A">Projet A</SelectItem>
                      <SelectItem value="Projet B">Projet B</SelectItem>
                      <SelectItem value="Interne">Interne</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-1">
                  <Label htmlFor="task">Tâche</Label>
                  <Select value={addTask} onValueChange={setAddTask}>
                    <SelectTrigger id="task" aria-label="Tâche">
                      <SelectValue placeholder="Sélectionner une tâche" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Développement">Développement</SelectItem>
                      <SelectItem value="Design">Design</SelectItem>
                      <SelectItem value="Gestion de projet">Gestion de projet</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="grid gap-1">
                    <Label htmlFor="start">Début</Label>
                    <Input id="start" name="start" type="date" required />
                  </div>
                  <div className="grid gap-1">
                    <Label htmlFor="end">Fin</Label>
                    <Input id="end" name="end" type="date" required />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit">Ajouter</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        <Dialog open={!!editTarget} onOpenChange={(open) => { if (!open) setEditTarget(null); }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Modifier le prévisionnel</DialogTitle>
            </DialogHeader>
            {editTarget ? (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const fd = new FormData(e.currentTarget);
                  const hours = Number(fd.get('hours') || 0);
                  if (!isNaN(hours)) {
                    updateForecastEntry(editTarget.userId, editTarget.date, editTarget.index, hours);
                    setEditTarget(null);
                  }
                }}
                className="space-y-3"
              >
                <div className="grid gap-1">
                  <Label htmlFor="hours">Heures</Label>
                  <Input
                    id="hours"
                    name="hours"
                    type="number"
                    min={0}
                    step={0.5}
                    defaultValue={
                      forecastEntries[editTarget.userId]?.[editTarget.date]?.[editTarget.index]?.hours ?? 7
                    }
                  />
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    variant="destructive"
                    onClick={() => {
                      deleteForecastEntry(editTarget.userId, editTarget.date, editTarget.index);
                      setEditTarget(null);
                    }}
                  >
                    Supprimer
                  </Button>
                  <Button type="submit">Enregistrer</Button>
                </DialogFooter>
              </form>
            ) : null}
          </DialogContent>
        </Dialog>
      </section>
    </AppLayout>
  );
}

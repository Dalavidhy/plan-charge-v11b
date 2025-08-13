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
import forecastService, { ForecastProject, ForecastData, ForecastEntry } from "@/services/forecast.service";
import { useToast } from "@/hooks/use-toast"

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
  const [forecastData, setForecastData] = useState<ForecastData | null>(null);
  const [projects, setProjects] = useState<ForecastProject[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);

  const { year, monthIndex } = useMemo(() => ({
    year: parseInt(month.split("-")[0]),
    monthIndex: parseInt(month.split("-")[1]) - 1,
  }), [month]);

  const days = useMemo(() => getDaysInMonth(year, monthIndex), [year, monthIndex]);
  const monthKey = `${year}-${String(monthIndex+1).padStart(2,'0')}`;
  const actifs = state.collaborateurs.filter(c => c.actif);

  // Gestion de l'ouverture/fermeture des lignes détaillées
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  // Helper function to create date key
  const dateKey = (d: number) => `${year}-${String(monthIndex+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;

  // Dialogs state
  const [addOpen, setAddOpen] = useState(false);
  const [addUser, setAddUser] = useState<string | null>(null);
  const [addCollaboratorId, setAddCollaboratorId] = useState<string | null>(null);
  const [addProject, setAddProject] = useState<string>("");
  const [addTask, setAddTask] = useState<string>("");
  const [selectedProject, setSelectedProject] = useState<ForecastProject | null>(null);
  const [editTarget, setEditTarget] = useState<{ forecastId: string; hours: number; description?: string } | null>(null);

  // Fetch projects for forecast dialog
  const fetchProjects = async () => {
    setLoadingProjects(true);
    try {
      // Get all projects and tasks (including inactive ones) for planning purposes
      const projectsData = await forecastService.getProjectsWithTasks(false);
      setProjects(projectsData);
    } catch (error) {
      console.error('Error fetching projects:', error);
      toast({
        title: "Erreur",
        description: "Impossible de charger les projets",
        variant: "destructive",
      });
    } finally {
      setLoadingProjects(false);
    }
  };

  // Fetch forecast data
  const fetchForecastData = async () => {
    try {
      const data = await forecastService.getForecasts(year, monthIndex + 1);
      setForecastData(data);
    } catch (error) {
      console.error('Error fetching forecast data:', error);
      // Silent fail - forecasts are optional
    }
  };

  // Add forecast range
  const addForecastRange = async (collaboratorId: string, projectId: string, taskId: string | null, startStr: string, endStr: string, description?: string) => {
    try {
      const result = await forecastService.createForecastBatch({
        collaborator_id: collaboratorId,
        project_id: projectId,
        task_id: taskId || undefined,
        start_date: startStr,
        end_date: endStr,
        hours_per_day: 7,
        description
      });
      
      toast({
        title: "Succès",
        description: `${result.created} prévisionnels créés, ${result.updated} mis à jour`,
      });
      
      // Refresh forecast data
      await fetchForecastData();
    } catch (error) {
      console.error('Error creating forecast:', error);
      toast({
        title: "Erreur",
        description: "Impossible de créer le prévisionnel",
        variant: "destructive",
      });
    }
  };

  // Update forecast entry
  const updateForecastEntry = async (forecastId: string, hours: number, description?: string) => {
    try {
      await forecastService.updateForecast(forecastId, { hours, description });
      
      toast({
        title: "Succès",
        description: "Prévisionnel mis à jour",
      });
      
      // Refresh forecast data
      await fetchForecastData();
    } catch (error) {
      console.error('Error updating forecast:', error);
      toast({
        title: "Erreur",
        description: "Impossible de mettre à jour le prévisionnel",
        variant: "destructive",
      });
    }
  };

  // Delete forecast entry
  const deleteForecastEntry = async (forecastId: string) => {
    try {
      await forecastService.deleteForecast(forecastId);
      
      toast({
        title: "Succès",
        description: "Prévisionnel supprimé",
      });
      
      // Refresh forecast data
      await fetchForecastData();
    } catch (error) {
      console.error('Error deleting forecast:', error);
      toast({
        title: "Erreur",
        description: "Impossible de supprimer le prévisionnel",
        variant: "destructive",
      });
    }
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
    fetchForecastData();
  }, [year, monthIndex]);

  // Fetch projects once on mount
  useEffect(() => {
    fetchProjects();
  }, []);

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
                          onClick={() => { 
                            // Find the matching Gryzzly collaborator ID
                            const gryzzlyCollab = planChargeData?.collaborators.find(
                              pc => pc.email.toLowerCase() === c.email.toLowerCase()
                            );
                            if (gryzzlyCollab) {
                              setAddUser(c.id);
                              setAddCollaboratorId(gryzzlyCollab.collaborator_id);
                              setAddProject("");
                              setAddTask("");
                              setSelectedProject(null);
                              setAddOpen(true);
                            } else {
                              toast({
                                title: "Erreur",
                                description: "Ce collaborateur n'est pas synchronisé avec Gryzzly",
                                variant: "destructive",
                              });
                            }
                          }}
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

                      // Get forecast data for this collaborator
                      const collabForecasts: Record<string, Record<string, number>> = {};
                      const forecastMeta: Record<string, { forecastId: string; description?: string }> = {};
                      
                      if (forecastData && planChargeCollab) {
                        const collabForecast = forecastData.collaborators.find(
                          fc => fc.collaborator_id === planChargeCollab.collaborator_id
                        );
                        
                        if (collabForecast) {
                          Object.entries(collabForecast.forecasts).forEach(([date, forecasts]) => {
                            forecasts.forEach(forecast => {
                              const label = forecast.task_name 
                                ? `${forecast.project_name} – ${forecast.task_name}`
                                : forecast.project_name;
                              
                              if (!collabForecasts[label]) collabForecasts[label] = {};
                              collabForecasts[label][date] = (collabForecasts[label][date] || 0) + forecast.hours;
                              
                              // Store metadata for editing
                              const metaKey = `${date}-${label}`;
                              forecastMeta[metaKey] = { 
                                forecastId: forecast.id, 
                                description: forecast.description 
                              };
                            });
                          });
                        }
                      }
                      
                      const forecastLines = Object.entries(collabForecasts).map(([label, hoursByDay]) => ({
                        label,
                        kind: 'forecast' as const,
                        hoursByDay,
                        meta: forecastMeta
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
                                if (isEditable && 'meta' in line) {
                                  const metaKey = `${dk}-${line.label}`;
                                  const meta = line.meta?.[metaKey];
                                  return (
                                    <td
                                      key={`${c.id}-line-${li}-${day.d}`}
                                      className={`${baseCell} ${color} cursor-pointer`}
                                      onClick={() => {
                                        if (meta) {
                                          setEditTarget({ 
                                            forecastId: meta.forecastId, 
                                            hours,
                                            description: meta.description 
                                          });
                                        }
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
              onSubmit={async (e) => {
                e.preventDefault();
                const fd = new FormData(e.currentTarget);
                const start = String(fd.get('start') || '');
                const end = String(fd.get('end') || '');
                const description = String(fd.get('description') || '');
                
                if (addCollaboratorId && addProject && start && end) {
                  await addForecastRange(
                    addCollaboratorId, 
                    addProject, 
                    addTask || null, 
                    start, 
                    end,
                    description || undefined
                  );
                  setAddOpen(false);
                  setAddProject("");
                  setAddTask("");
                  setSelectedProject(null);
                }
              }}
              className="space-y-3"
            >
              <div className="grid gap-3">
                <div className="grid gap-1">
                  <Label htmlFor="project">Projet</Label>
                  {loadingProjects ? (
                    <div className="flex items-center justify-center py-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="ml-2 text-sm">Chargement des projets...</span>
                    </div>
                  ) : (
                    <Select 
                      value={addProject} 
                      onValueChange={(value) => {
                        setAddProject(value);
                        const project = projects.find(p => p.id === value);
                        setSelectedProject(project || null);
                        setAddTask("");
                      }}
                    >
                      <SelectTrigger id="project" aria-label="Projet">
                        <SelectValue placeholder="Sélectionner un projet" />
                      </SelectTrigger>
                      <SelectContent>
                        {projects.length === 0 ? (
                          <SelectItem value="none" disabled>
                            Aucun projet disponible
                          </SelectItem>
                        ) : (
                          projects.map((project) => (
                            <SelectItem key={project.id} value={project.id}>
                              {project.name}
                              {project.code && ` (${project.code})`}
                              {!project.is_active && " - Inactif"}
                            </SelectItem>
                          ))
                        )}
                      </SelectContent>
                    </Select>
                  )}
                </div>
                <div className="grid gap-1">
                  <Label htmlFor="task">Tâche (optionnel)</Label>
                  <Select 
                    value={addTask} 
                    onValueChange={setAddTask}
                    disabled={!selectedProject || selectedProject.tasks.length === 0}
                  >
                    <SelectTrigger id="task" aria-label="Tâche">
                      <SelectValue placeholder="Sélectionner une tâche" />
                    </SelectTrigger>
                    <SelectContent>
                      {selectedProject?.tasks.length === 0 ? (
                        <SelectItem value="none" disabled>
                          Aucune tâche disponible
                        </SelectItem>
                      ) : (
                        selectedProject?.tasks.map((task) => (
                          <SelectItem key={task.id} value={task.id}>
                            {task.name}
                            {task.code && ` (${task.code})`}
                            {!task.is_active && " - Inactive"}
                          </SelectItem>
                        ))
                      )}
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
                <div className="grid gap-1">
                  <Label htmlFor="description">Description (optionnel)</Label>
                  <Input id="description" name="description" type="text" placeholder="Description du prévisionnel" />
                </div>
              </div>
              <DialogFooter>
                <Button type="submit" disabled={loadingProjects || !addProject}>
                  Ajouter
                </Button>
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
                onSubmit={async (e) => {
                  e.preventDefault();
                  const fd = new FormData(e.currentTarget);
                  const hours = Number(fd.get('hours') || 0);
                  const description = String(fd.get('description') || '');
                  if (!isNaN(hours) && hours > 0) {
                    await updateForecastEntry(
                      editTarget.forecastId, 
                      hours, 
                      description || undefined
                    );
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
                    defaultValue={editTarget.hours || 7}
                  />
                </div>
                <div className="grid gap-1">
                  <Label htmlFor="description">Description (optionnel)</Label>
                  <Input
                    id="description"
                    name="description"
                    type="text"
                    defaultValue={editTarget.description || ''}
                    placeholder="Description du prévisionnel"
                  />
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    variant="destructive"
                    onClick={async () => {
                      await deleteForecastEntry(editTarget.forecastId);
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

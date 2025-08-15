import React, { useEffect, useMemo, useState } from "react";
import Holidays from "date-holidays";
import AppLayout from "@/layouts/AppLayout";
import { useAppStore } from "@/store/AppStore";
import { setSEO } from "@/lib/seo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ChevronDown, ChevronRight, ChevronLeft, Plus, Loader2, AlertCircle } from "lucide-react";
import planChargeService, { PlanChargeData, PlanChargeCollaborator } from "@/services/plancharge.service";
import forecastService, { ForecastProject, ForecastData, ForecastEntry, ForecastGroup } from "@/services/forecast.service";
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
  
  // Calculate global metrics
  const globalMetrics = useMemo(() => {
    let totalWorkingDays = 0;
    let totalAbsenceDays = 0;
    let totalImputedDays = 0;
    let totalForecastDays = 0;
    let totalNotPlannedDays = 0;
    let collaboratorsWithIssues = 0;
    
    // Daily statistics for the footer
    const dailyStats: Record<string, { available: number; planned: number }> = {};
    
    actifs.forEach(c => {
      const planChargeCollab = planChargeData?.collaborators.find(
        pc => pc.email.toLowerCase() === c.email.toLowerCase()
      );
      
      let collabWorkingDays = 0;
      let collabAbsenceDays = 0;
      let collabImputedDays = 0;
      let collabForecastDays = 0;
      let collabNotPlannedDays = 0;
      
      days.forEach(day => {
        if (!day.isWeekend && !day.isHoliday) {
          collabWorkingDays++;
          const dk = `${year}-${String(monthIndex+1).padStart(2,'0')}-${String(day.d).padStart(2,'0')}`;
          
          // Initialize daily stats
          if (!dailyStats[dk]) {
            dailyStats[dk] = { available: 0, planned: 0 };
          }
          
          // Check for absence
          const hasAbsence = planChargeCollab?.absences?.some(absence => {
            const absStart = new Date(absence.start_date);
            const absEnd = new Date(absence.end_date);
            const checkDate = new Date(dk);
            return checkDate >= absStart && checkDate <= absEnd;
          }) || false;
          
          // Check for declarations (imputations)
          const declarations = planChargeCollab?.declarations?.[dk] || [];
          const hasDeclarations = declarations.length > 0;
          
          // Check for forecasts
          let hasForecast = false;
          if (forecastData && planChargeCollab) {
            const collabForecast = forecastData.collaborators.find(
              fc => fc.collaborator_id === planChargeCollab.collaborator_id
            );
            if (collabForecast && collabForecast.forecasts[dk]) {
              hasForecast = collabForecast.forecasts[dk].length > 0;
            }
          }
          
          if (hasAbsence) {
            collabAbsenceDays++;
            dailyStats[dk].planned++; // Absence counts as planned
          } else {
            dailyStats[dk].available++;
            if (hasDeclarations) {
              collabImputedDays++;
              dailyStats[dk].planned++;
            } else if (hasForecast) {
              collabForecastDays++;
              dailyStats[dk].planned++;
            } else {
              collabNotPlannedDays++;
            }
          }
        }
      });
      
      // Calculate TACE for this collaborator
      const availableDays = collabWorkingDays - collabAbsenceDays;
      const plannedDays = collabImputedDays + collabForecastDays + collabAbsenceDays;
      const tacePercentage = availableDays > 0 
        ? Math.round(((plannedDays - collabAbsenceDays) / availableDays) * 100)
        : 0;
      
      // Check if collaborator has staffing issues
      if (tacePercentage < 50 || collabNotPlannedDays > 3) {
        collaboratorsWithIssues++;
      }
      
      // Aggregate totals
      totalWorkingDays += collabWorkingDays;
      totalAbsenceDays += collabAbsenceDays;
      totalImputedDays += collabImputedDays;
      totalForecastDays += collabForecastDays;
      totalNotPlannedDays += collabNotPlannedDays;
    });
    
    const totalAvailableDays = totalWorkingDays - totalAbsenceDays;
    const globalTACE = totalAvailableDays > 0 
      ? Math.round(((totalImputedDays + totalForecastDays) / totalAvailableDays) * 100)
      : 0;
    
    const imputedPercentage = totalWorkingDays > 0 
      ? Math.round((totalImputedDays / totalWorkingDays) * 100)
      : 0;
    const forecastPercentage = totalWorkingDays > 0 
      ? Math.round((totalForecastDays / totalWorkingDays) * 100)
      : 0;
    const notPlannedPercentage = totalWorkingDays > 0 
      ? Math.round((totalNotPlannedDays / totalWorkingDays) * 100)
      : 0;
    
    return {
      globalTACE,
      collaboratorsWithIssues,
      imputedPercentage,
      forecastPercentage,
      notPlannedPercentage,
      dailyStats
    };
  }, [actifs, planChargeData, forecastData, days, year, monthIndex]);

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
  const [editGroup, setEditGroup] = useState<ForecastGroup | null>(null);
  const [editMode, setEditMode] = useState(false);

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


  // Handle forecast click - get the group and open edit dialog
  const handleForecastClick = async (forecastId: string) => {
    try {
      const group = await forecastService.getForecastGroup(forecastId);
      setEditGroup(group);
      setEditMode(true);
      setAddCollaboratorId(group.collaborator_id);
      setAddProject(group.project_id);
      setAddTask(group.task_id || "");
      
      // Find and set the selected project
      const project = projects.find(p => p.id === group.project_id);
      setSelectedProject(project || null);
      
      setAddOpen(true);
    } catch (error) {
      console.error('Error fetching forecast group:', error);
      toast({
        title: "Erreur",
        description: "Impossible de récupérer les informations du prévisionnel",
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

  // Show error message if collaborators failed to load
  if (state.collaborateursError) {
    return (
      <AppLayout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="text-red-600 mb-4">
              <AlertCircle className="mx-auto h-12 w-12" />
            </div>
            <h2 className="text-xl font-semibold mb-2">Erreur de chargement</h2>
            <p className="text-muted-foreground mb-4">{state.collaborateursError}</p>
            <Button onClick={() => window.location.reload()}>Actualiser la page</Button>
          </div>
        </div>
      </AppLayout>
    );
  }
  
  // Show loading state while collaborators are being loaded
  if (state.collaborateursLoading || (state.collaborateurs.length === 0 && !state.collaborateursError)) {
    return (
      <AppLayout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="mx-auto h-12 w-12 animate-spin text-primary" />
            <p className="mt-4 text-muted-foreground">Chargement des collaborateurs...</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout title="Plan de charge">
      <section className="space-y-4">
        {/* KPI Bar */}
        {globalMetrics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600 mb-1">TACE Global</div>
              <div className={`text-2xl font-bold ${
                globalMetrics.globalTACE >= 80 ? 'text-green-600' :
                globalMetrics.globalTACE >= 50 ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {globalMetrics.globalTACE}%
              </div>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600 mb-1">Collaborateurs sans staffing suffisant</div>
              <div className={`text-2xl font-bold ${
                globalMetrics.collaboratorsWithIssues === 0 ? 'text-green-600' :
                globalMetrics.collaboratorsWithIssues <= 2 ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {globalMetrics.collaboratorsWithIssues}
              </div>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600 mb-1">Répartition des activités</div>
              <div className="flex items-center space-x-2 text-sm">
                <span className="text-green-600 font-semibold">{globalMetrics.imputedPercentage}%</span>
                <span className="text-gray-400">/</span>
                <span className="text-blue-600 font-semibold">{globalMetrics.forecastPercentage}%</span>
                <span className="text-gray-400">/</span>
                <span className="text-red-600 font-semibold">{globalMetrics.notPlannedPercentage}%</span>
              </div>
              <div className="text-xs text-gray-500 mt-1">Imputé / Prévisionnel / Non planifié</div>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600 mb-1">Équipe</div>
              <div className="text-2xl font-bold text-gray-700">
                {actifs.length} collaborateurs
              </div>
            </div>
          </div>
        )}
        
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
                <th className="px-3 py-2 text-left w-80">Collaborateur</th>
                {days.map((day) => (
                  <th key={day.d} className={`px-2 py-2 text-center font-medium ${day.isWeekend || day.isHoliday ? 'text-muted-foreground' : ''}`}>
                    <div className="flex flex-col items-center">
                      <span>{day.label}</span>
                      <span className="tabular-nums">{day.d}</span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {actifs.map((c) => {
                // Find matching collaborator in plan charge data
                const planChargeCollab = planChargeData?.collaborators.find(
                  pc => pc.email.toLowerCase() === c.email.toLowerCase()
                );
                
                // Calculate TACE metrics for this collaborator
                let workingDays = 0;
                let daysWithAbsence = 0;
                let daysWithActivity = 0;
                let daysNotPlanned = 0;
                
                days.forEach(day => {
                  if (!day.isWeekend && !day.isHoliday) {
                    workingDays++;
                    const dk = dateKey(day.d);
                    
                    // Check for absence
                    const hasAbsence = planChargeCollab?.absences?.some(absence => {
                      const absStart = new Date(absence.start_date);
                      const absEnd = new Date(absence.end_date);
                      const checkDate = new Date(dk);
                      return checkDate >= absStart && checkDate <= absEnd;
                    }) || false;
                    
                    // Check for declarations (imputations)
                    const declarations = planChargeCollab?.declarations?.[dk] || [];
                    const hasDeclarations = declarations.length > 0;
                    
                    // Check for forecasts
                    let hasForecast = false;
                    if (forecastData && planChargeCollab) {
                      const collabForecast = forecastData.collaborators.find(
                        fc => fc.collaborator_id === planChargeCollab.collaborator_id
                      );
                      if (collabForecast && collabForecast.forecasts[dk]) {
                        hasForecast = collabForecast.forecasts[dk].length > 0;
                      }
                    }
                    
                    if (hasAbsence) {
                      daysWithAbsence++;
                      daysWithActivity++; // Absence counts as planned activity
                    } else if (hasDeclarations || hasForecast) {
                      daysWithActivity++;
                    } else {
                      daysNotPlanned++;
                    }
                  }
                });
                
                // Calculate TACE percentage
                const availableDays = workingDays - daysWithAbsence;
                const tacePercentage = availableDays > 0 
                  ? Math.round(((daysWithActivity - daysWithAbsence) / availableDays) * 100)
                  : 0;
                
                // Determine colors
                const taceColor = tacePercentage >= 80 ? 'bg-green-100 text-green-800' :
                                 tacePercentage >= 50 ? 'bg-orange-100 text-orange-800' :
                                 'bg-red-100 text-red-800';
                const nameColor = daysNotPlanned > 3 ? 'text-red-600 font-semibold' : '';
                
                return (
                  <React.Fragment key={c.id}>
                    <tr key={`${c.id}-main`} className="border-t">
                      <td className="px-3 py-2 font-medium">
                        <div className="flex items-center">
                          <button
                            type="button"
                            aria-expanded={!!expanded[c.id]}
                            onClick={() => setExpanded((prev) => ({ ...prev, [c.id]: !prev[c.id] }))}
                            className="inline-flex items-center justify-center rounded-md border bg-background hover:bg-accent hover:text-accent-foreground mr-2 h-6 w-6 flex-shrink-0"
                            title={expanded[c.id] ? "Réduire" : "Détails"}
                          >
                            {expanded[c.id] ? (
                              <ChevronDown className="w-4 h-4" />
                            ) : (
                              <ChevronRight className="w-4 h-4" />
                            )}
                          </button>
                          <span className={`flex-grow ${nameColor}`}>{c.nom}</span>
                          <span className={`ml-2 inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ${taceColor}`}>
                            {tacePercentage}%
                          </span>
                          {daysNotPlanned > 0 && (
                            <span className="ml-1 inline-flex items-center rounded-md bg-red-100 px-2 py-1 text-xs font-medium text-red-800">
                              {daysNotPlanned}j
                            </span>
                          )}
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="ml-2 flex-shrink-0"
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
                              setEditMode(false);
                              setEditGroup(null);
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
                        </div>
                      </td>
                      {days.map((day) => {
                        const dk = dateKey(day.d);
                        const declarations = planChargeCollab?.declarations?.[dk] || [];
                        const dayHours = planChargeService.calculateDayHours(
                          declarations,
                          planChargeCollab?.absences || [],
                          dk
                        );
                        
                        // Check for forecasts
                        let forecastHours = 0;
                        if (forecastData && planChargeCollab) {
                          const collabForecast = forecastData.collaborators.find(
                            fc => fc.collaborator_id === planChargeCollab.collaborator_id
                          );
                          if (collabForecast && collabForecast.forecasts[dk]) {
                            forecastHours = collabForecast.forecasts[dk].reduce((sum, f) => sum + f.hours, 0);
                          }
                        }
                        
                        // Determine what to show and color
                        let displayValue = null;
                        let colorClass = '';
                        
                        if (!day.isWeekend && !day.isHoliday) {
                          if (dayHours.hasAbsence) {
                            // Absence - show in green
                            displayValue = 7; // Or actual absence hours if partial
                            colorClass = 'bg-green-100 text-green-800';
                          } else if (dayHours.totalProjectHours > 0) {
                            // Imputation - show in green
                            displayValue = dayHours.totalProjectHours;
                            colorClass = 'bg-green-100 text-green-800';
                          } else if (forecastHours > 0) {
                            // Forecast - show in blue
                            displayValue = forecastHours;
                            colorClass = 'bg-blue-100 text-blue-800';
                          } else {
                            // Nothing planned - show 0 in red
                            displayValue = 0;
                            colorClass = 'bg-red-100 text-red-800';
                          }
                        }
                        
                        return (
                          <td key={`${c.id}-${day.d}`} className={`h-8 text-center ${day.isWeekend || day.isHoliday ? 'bg-muted' : ''}`}>
                            {displayValue !== null ? (
                              <span className={`mx-auto inline-flex items-center justify-center rounded-sm px-1.5 py-0.5 text-xs tabular-nums ${colorClass}`}>
                                {displayValue}
                              </span>
                            ) : null}
                          </td>
                        )
                      })}
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
                                    ? line.kind === 'forecast'
                                      ? 'bg-blue-50 text-blue-700'  // Blue for forecasts
                                      : 'bg-green-50 text-green-700' // Green for imputations and absences
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
                                          handleForecastClick(meta.forecastId);
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
                            </tr>
                          ))}
                        </>
                      );
                    })()}

                  </React.Fragment>
                );
              })}
            </tbody>
            {/* Totals row */}
            {globalMetrics && (
              <tfoot className="border-t-2 border-gray-300 bg-gray-50">
                <tr>
                  <td className="px-3 py-2 font-semibold">Totaux journaliers</td>
                  {days.map((day) => {
                    const dk = dateKey(day.d);
                    const stats = globalMetrics.dailyStats[dk];
                    if (!stats || day.isWeekend || day.isHoliday) {
                      return (
                        <td key={`total-${day.d}`} className="h-10 text-center bg-muted">
                          -
                        </td>
                      );
                    }
                    const coverage = stats.available > 0 
                      ? Math.round((stats.planned / stats.available) * 100)
                      : 0;
                    const color = coverage >= 80 ? 'text-green-700' :
                                coverage >= 50 ? 'text-orange-600' : 'text-red-600';
                    return (
                      <td key={`total-${day.d}`} className="h-10 text-center">
                        <div className="flex flex-col items-center">
                          <span className={`text-xs font-semibold ${color}`}>
                            {coverage}%
                          </span>
                          <span className="text-xs text-gray-500">
                            {stats.planned}/{stats.available}
                          </span>
                        </div>
                      </td>
                    );
                  })}
                </tr>
              </tfoot>
            )}
          </table>
          )}
        </div>
        {/* Dialogs */}
        <Dialog open={addOpen} onOpenChange={(open) => {
          setAddOpen(open);
          if (!open) {
            setEditMode(false);
            setEditGroup(null);
          }
        }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editMode ? "Modifier le prévisionnel" : "Ajouter un prévisionnel"}</DialogTitle>
            </DialogHeader>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const fd = new FormData(e.currentTarget);
                const start = String(fd.get('start') || '');
                const end = String(fd.get('end') || '');
                const description = String(fd.get('description') || '');
                
                if (addCollaboratorId && addProject && start && end) {
                  if (editMode && editGroup) {
                    // Delete old group and create new one
                    await forecastService.deleteForecastGroup(editGroup.forecast_ids);
                  }
                  
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
                  setEditMode(false);
                  setEditGroup(null);
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
                    <Input 
                      id="start" 
                      name="start" 
                      type="date" 
                      required 
                      defaultValue={editGroup?.start_date || ''}
                    />
                  </div>
                  <div className="grid gap-1">
                    <Label htmlFor="end">Fin</Label>
                    <Input 
                      id="end" 
                      name="end" 
                      type="date" 
                      required 
                      defaultValue={editGroup?.end_date || ''}
                    />
                  </div>
                </div>
                <div className="grid gap-1">
                  <Label htmlFor="description">Description (optionnel)</Label>
                  <Input 
                    id="description" 
                    name="description" 
                    type="text" 
                    placeholder="Description du prévisionnel" 
                    defaultValue={editGroup?.description || ''}
                  />
                </div>
              </div>
              <DialogFooter>
                {editMode && (
                  <Button 
                    type="button" 
                    variant="destructive"
                    onClick={async () => {
                      if (editGroup) {
                        await forecastService.deleteForecastGroup(editGroup.forecast_ids);
                        await fetchForecastData();
                        setAddOpen(false);
                        setEditMode(false);
                        setEditGroup(null);
                        toast({
                          title: "Succès",
                          description: "Prévisionnel supprimé",
                        });
                      }
                    }}
                  >
                    Supprimer
                  </Button>
                )}
                <Button type="submit" disabled={loadingProjects || !addProject}>
                  {editMode ? "Modifier" : "Ajouter"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

      </section>
    </AppLayout>
  );
}

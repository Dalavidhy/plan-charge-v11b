import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, ChevronDown, Loader2, AlertCircle } from "lucide-react";
import AppLayout from "@/layouts/AppLayout";
import { Button } from "@/components/ui/button";
import { setSEO } from "@/lib/seo";
import { Alert, AlertDescription } from "@/components/ui/alert";
import trService, { TRMonthData, TREmployee } from "@/services/tr.service";
import { toast } from "sonner";

export default function DroitsTR() {
  const now = new Date();
  const [month, setMonth] = useState<string>(`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<TRMonthData | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  const { year, monthIndex } = {
    year: parseInt(month.split("-")[0]),
    monthIndex: parseInt(month.split("-")[1]) - 1,
  };

  const monthKey = `${year}-${String(monthIndex+1).padStart(2,'0')}`;

  useEffect(() => {
    setSEO({
      title: `Droits Titres-Restaurant – ${monthKey}`,
      description: "Calcul automatique des droits TR basé sur les absences Payfit.",
      canonical: "/droits-tr",
    });
  }, [monthKey]);

  useEffect(() => {
    loadTRData();
  }, [year, monthIndex]);

  const loadTRData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await trService.getTRRights(year, monthIndex + 1);
      setData(result);
    } catch (err) {
      const errorMessage = 'Erreur lors du chargement des données TR';
      setError(errorMessage);
      toast.error(errorMessage);
      console.error('Error loading TR data:', err);
    } finally {
      setLoading(false);
    }
  };

  const exportCSV = async () => {
    try {
      await trService.downloadTRRights(year, monthIndex + 1);
      toast.success('Export CSV généré avec succès');
    } catch (err) {
      toast.error('Erreur lors de l\'export CSV');
      console.error('Error exporting CSV:', err);
    }
  };

  const getAbsenceTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      'fr_conges_payes': 'Congés payés',
      'fr_rtt': 'RTT',
      'fr_maladie_ordinaire': 'Maladie',
      'fr_sans_solde': 'Sans solde',
      'fr_deces': 'Décès famille',
      'fr_mariage': 'Mariage',
    };
    return labels[type] || type;
  };

  const formatDate = (dateStr: string): string => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <AppLayout title="Droits Titres-Restaurant">
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="w-8 h-8 animate-spin" />
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout title="Droits Titres-Restaurant">
      <section className="space-y-4">
        <div className="flex flex-col gap-2">
          <div>
            <h2 className="text-xl font-semibold">Calcul automatique des droits TR</h2>
            <p className="text-sm text-muted-foreground">Basé sur les jours ouvrés et les absences Payfit</p>
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
            <div className="text-sm text-muted-foreground">
              {data && (
                <>
                  Jours ouvrés: {data.working_days}
                  {data.holidays.length > 0 && ` (${data.holidays.length} jour${data.holidays.length > 1 ? 's' : ''} férié${data.holidays.length > 1 ? 's' : ''})`}
                </>
              )}
            </div>
            <div className="flex items-center gap-3">
              <Button onClick={loadTRData} variant="outline">
                Actualiser
              </Button>
              <Button onClick={exportCSV}>
                Exporter CSV
              </Button>
            </div>
          </div>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {data && (
          <div className="rounded-lg border shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-card">
                <tr>
                  <th className="px-3 py-2 text-left">Matricule</th>
                  <th className="px-3 py-2 text-left">Nom</th>
                  <th className="px-3 py-2 text-left">Prénom</th>
                  <th className="px-3 py-2 text-center">Jours absences</th>
                  <th className="px-3 py-2 text-center">Droits TR</th>
                </tr>
              </thead>
              <tbody>
                {data.employees.map((employee: TREmployee) => (
                  <>
                    <tr key={employee.email} className="border-t hover:bg-accent/50">
                      <td className="px-3 py-2">{employee.matricule}</td>
                      <td className="px-3 py-2 font-medium">
                        <button
                          type="button"
                          aria-expanded={!!expanded[employee.email]}
                          onClick={() => setExpanded((prev) => ({ ...prev, [employee.email]: !prev[employee.email] }))}
                          className="inline-flex items-center gap-2 hover:underline"
                        >
                          {expanded[employee.email] ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                          {employee.last_name?.toUpperCase()}
                        </button>
                      </td>
                      <td className="px-3 py-2">{employee.first_name}</td>
                      <td className="px-3 py-2 text-center">
                        {employee.absence_days > 0 ? (
                          <span className="text-orange-600 font-medium">{employee.absence_days}</span>
                        ) : (
                          <span className="text-muted-foreground">0</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-center">
                        <span className="font-bold text-lg">
                          {employee.tr_rights}
                        </span>
                      </td>
                    </tr>
                    {expanded[employee.email] && (
                      <tr key={`${employee.email}-details`} className="border-t bg-accent/20">
                        <td className="px-3 py-3" colSpan={5}>
                          <div className="pl-8 space-y-2">
                            <div className="font-medium">Détail du calcul</div>
                            <div className="text-sm text-muted-foreground">
                              Jours ouvrés: {employee.working_days} − Absences: {employee.absence_days} = <span className="font-medium">{employee.tr_rights} titres restaurant</span>
                            </div>
                            
                            {employee.absences.length > 0 && (
                              <>
                                <div className="font-medium mt-3">Absences Payfit du mois</div>
                                <ul className="space-y-1 text-sm">
                                  {employee.absences.map((absence, idx) => (
                                    <li key={idx} className="flex items-center justify-between max-w-xl">
                                      <span>
                                        {formatDate(absence.start_date)}
                                        {absence.end_date !== absence.start_date && ` au ${formatDate(absence.end_date)}`}
                                      </span>
                                      <span className="text-muted-foreground">
                                        {getAbsenceTypeLabel(absence.type)} — {absence.working_days_in_month} jour{absence.working_days_in_month > 1 ? 's' : ''}
                                      </span>
                                    </li>
                                  ))}
                                </ul>
                              </>
                            )}
                            
                            {employee.absences.length === 0 && (
                              <div className="text-sm text-muted-foreground">
                                Aucune absence ce mois
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </AppLayout>
  );
}
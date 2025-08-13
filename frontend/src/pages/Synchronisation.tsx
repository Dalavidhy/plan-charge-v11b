import { useEffect } from "react";
import AppLayout from "@/layouts/AppLayout";
import { useAppStore } from "@/store/AppStore";
import { setSEO } from "@/lib/seo";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import PayfitDashboard from "@/pages/PayfitDashboard";
import GryzzlyDashboard from "@/pages/GryzzlyDashboard";

function formatDuration(start: string, end: string) {
  const d = new Date(end).getTime() - new Date(start).getTime();
  if (Number.isNaN(d) || d < 0) return "—";
  const s = Math.round(d / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const rs = s % 60;
  return rs ? `${m}m${rs}s` : `${m}m`;
}

export default function Synchronisation() {
  const { state } = useAppStore();

  useEffect(() => {
    setSEO({
      title: "Synchronisation",
      description: "Historique des synchronisations + détails Payfit & Gryzzly",
      canonical: "/sync",
    });
  }, []);

  return (
    <AppLayout title="Synchronisation">
      <Tabs defaultValue="history">
        <TabsList>
          <TabsTrigger value="history">Historique</TabsTrigger>
          <TabsTrigger value="payfit">Payfit</TabsTrigger>
          <TabsTrigger value="gryzzly">Gryzzly</TabsTrigger>
        </TabsList>

        <TabsContent value="history">
          <section aria-labelledby="history-heading">
            <h2 id="history-heading" className="sr-only">Historique des synchronisations</h2>
            <Card>
              <CardHeader>
                <CardTitle>Historique des synchronisations</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Début</TableHead>
                      <TableHead>Fin</TableHead>
                      <TableHead>Durée</TableHead>
                      <TableHead>Connecteur</TableHead>
                      <TableHead>Statut</TableHead>
                      <TableHead>Message</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(state.sync?.runs ?? []).length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center text-muted-foreground">Aucun run pour le moment.</TableCell>
                      </TableRow>
                    )}
                    {(state.sync?.runs ?? []).map((r) => (
                      <TableRow key={r.id}>
                        <TableCell>{new Date(r.startedAt).toLocaleString()}</TableCell>
                        <TableCell>{new Date(r.endedAt).toLocaleString()}</TableCell>
                        <TableCell>{formatDuration(r.startedAt, r.endedAt)}</TableCell>
                        <TableCell className="capitalize">{r.connector}</TableCell>
                        <TableCell>
                          {r.status === "success" ? (
                            <Badge variant="secondary">Succès</Badge>
                          ) : (
                            <Badge variant="destructive">Échec</Badge>
                          )}
                        </TableCell>
                        <TableCell>{r.message ?? ""}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </section>
        </TabsContent>

        <TabsContent value="payfit">
          <PayfitDashboard />
        </TabsContent>

        <TabsContent value="gryzzly">
          <GryzzlyDashboard />
        </TabsContent>
      </Tabs>
    </AppLayout>
  );
}

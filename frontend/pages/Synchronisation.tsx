import { useEffect } from "react";
import AppLayout from "@/layouts/AppLayout";
import { useAppStore } from "@/store/AppStore";
import { setSEO } from "@/lib/seo";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

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
          <section aria-labelledby="payfit-heading">
            <h2 id="payfit-heading" className="sr-only">Détails Payfit</h2>
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardHeader><CardTitle>Utilisateurs</CardTitle></CardHeader>
                <CardContent className="text-3xl font-semibold">{state.payfit?.counts.users ?? 0}</CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Contrats</CardTitle></CardHeader>
                <CardContent className="text-3xl font-semibold">{state.payfit?.counts.contracts ?? 0}</CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Absences</CardTitle></CardHeader>
                <CardContent className="text-3xl font-semibold">{state.payfit?.counts.absences ?? 0}</CardContent>
              </Card>
            </div>

            <div className="mt-6 space-y-6">
              <Card>
                <CardHeader><CardTitle>Utilisateurs</CardTitle></CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Nom</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>Statut</TableHead>
                        <TableHead>Dernière synchro</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(state.payfit?.users ?? []).map(u => (
                        <TableRow key={u.id}>
                          <TableCell>{u.nom}</TableCell>
                          <TableCell>{u.email}</TableCell>
                          <TableCell className="capitalize">{u.statut}</TableCell>
                          <TableCell>{u.syncedAt ? new Date(u.syncedAt).toLocaleString() : "—"}</TableCell>
                        </TableRow>
                      ))}
                      {(state.payfit?.users ?? []).length === 0 && (
                        <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">Aucun utilisateur.</TableCell></TableRow>
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle>Contrats</CardTitle></CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Intitulé</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Début</TableHead>
                        <TableHead>Fin</TableHead>
                        <TableHead>Dernière synchro</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(state.payfit?.contracts ?? []).map(c => (
                        <TableRow key={c.id}>
                          <TableCell>{c.intitulé}</TableCell>
                          <TableCell>{c.type}</TableCell>
                          <TableCell>{c.début ?? "—"}</TableCell>
                          <TableCell>{c.fin ?? "—"}</TableCell>
                          <TableCell>{c.syncedAt ? new Date(c.syncedAt).toLocaleString() : "—"}</TableCell>
                        </TableRow>
                      ))}
                      {(state.payfit?.contracts ?? []).length === 0 && (
                        <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground">Aucun contrat.</TableCell></TableRow>
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle>Absences</CardTitle></CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Collaborateur</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Du</TableHead>
                        <TableHead>Au</TableHead>
                        <TableHead>Heures</TableHead>
                        <TableHead>Source</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(state.payfit?.absences ?? []).map(a => (
                        <TableRow key={a.id}>
                          <TableCell>{a.collaborateur}</TableCell>
                          <TableCell>{a.type}</TableCell>
                          <TableCell>{a.du}</TableCell>
                          <TableCell>{a.au}</TableCell>
                          <TableCell>{a.heures ?? "—"}</TableCell>
                          <TableCell>{a.source ?? "—"}</TableCell>
                        </TableRow>
                      ))}
                      {(state.payfit?.absences ?? []).length === 0 && (
                        <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground">Aucune absence.</TableCell></TableRow>
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </div>
          </section>
        </TabsContent>

        <TabsContent value="gryzzly">
          <section aria-labelledby="gryzzly-heading">
            <h2 id="gryzzly-heading" className="sr-only">Détails Gryzzly</h2>
            <div className="grid gap-4 md:grid-cols-4">
              <Card>
                <CardHeader><CardTitle>Utilisateurs</CardTitle></CardHeader>
                <CardContent className="text-3xl font-semibold">{state.gryzzly?.counts.users ?? 0}</CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Déclarations</CardTitle></CardHeader>
                <CardContent className="text-3xl font-semibold">{state.gryzzly?.counts.declarations ?? 0}</CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Projets</CardTitle></CardHeader>
                <CardContent className="text-3xl font-semibold">{state.gryzzly?.counts.projects ?? 0}</CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Tâches</CardTitle></CardHeader>
                <CardContent className="text-3xl font-semibold">{state.gryzzly?.counts.tasks ?? 0}</CardContent>
              </Card>
            </div>

            <div className="mt-6 space-y-6">
              <Card>
                <CardHeader><CardTitle>Utilisateurs synchronisés</CardTitle></CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Nom</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>ID externe</TableHead>
                        <TableHead>Dernière synchro</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(state.gryzzly?.users ?? []).map(u => (
                        <TableRow key={u.id}>
                          <TableCell>{u.nom}</TableCell>
                          <TableCell>{u.email}</TableCell>
                          <TableCell>{u.externalId ?? "—"}</TableCell>
                          <TableCell>{u.syncedAt ? new Date(u.syncedAt).toLocaleString() : "—"}</TableCell>
                        </TableRow>
                      ))}
                      {(state.gryzzly?.users ?? []).length === 0 && (
                        <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">Aucun utilisateur.</TableCell></TableRow>
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle>Déclarations synchronisées</CardTitle></CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Collaborateur</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>Projet</TableHead>
                        <TableHead>Tâche</TableHead>
                        <TableHead>Heures</TableHead>
                        <TableHead>Statut</TableHead>
                        <TableHead>SyncAt</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(state.gryzzly?.declarations ?? []).map(d => (
                        <TableRow key={d.id}>
                          <TableCell>{d.collaborateur}</TableCell>
                          <TableCell>{d.date}</TableCell>
                          <TableCell>{d.projet}</TableCell>
                          <TableCell>{d.tache}</TableCell>
                          <TableCell>{d.heures}</TableCell>
                          <TableCell>{d.statut}</TableCell>
                          <TableCell>{d.syncedAt ? new Date(d.syncedAt).toLocaleString() : "—"}</TableCell>
                        </TableRow>
                      ))}
                      {(state.gryzzly?.declarations ?? []).length === 0 && (
                        <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground">Aucune déclaration.</TableCell></TableRow>
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle>Projets et tâches synchronisés</CardTitle></CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Projet</TableHead>
                        <TableHead>Tâche</TableHead>
                        <TableHead>Actif</TableHead>
                        <TableHead>Dernière synchro</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(state.gryzzly?.items ?? []).map(i => (
                        <TableRow key={i.id}>
                          <TableCell>{i.projet}</TableCell>
                          <TableCell>{i.tache}</TableCell>
                          <TableCell>{i.actif ? "Oui" : "Non"}</TableCell>
                          <TableCell>{i.syncedAt ? new Date(i.syncedAt).toLocaleString() : "—"}</TableCell>
                        </TableRow>
                      ))}
                      {(state.gryzzly?.items ?? []).length === 0 && (
                        <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">Aucun élément.</TableCell></TableRow>
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </div>
          </section>
        </TabsContent>
      </Tabs>
    </AppLayout>
  );
}

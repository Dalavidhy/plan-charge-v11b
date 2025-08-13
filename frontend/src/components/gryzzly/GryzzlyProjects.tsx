import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Loader2, Search, FolderOpen, DollarSign, Clock } from 'lucide-react';
import { toast } from 'sonner';
import gryzzlyService, { GryzzlyProject } from '@/services/gryzzly.service';

export default function GryzzlyProjects() {
  const [projects, setProjects] = useState<GryzzlyProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeOnly, setActiveOnly] = useState(false);
  const [billableOnly, setBillableOnly] = useState(false);

  useEffect(() => {
    loadProjects();
  }, [activeOnly, billableOnly]);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await gryzzlyService.getProjects({
        active_only: activeOnly,
        billable_only: billableOnly,
        limit: 500,
      });
      setProjects(data);
    } catch (error) {
      toast.error('Erreur lors du chargement des projets');
      console.error('Error loading projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredProjects = projects.filter(project => {
    const search = searchTerm.toLowerCase();
    return (
      project.name?.toLowerCase().includes(search) ||
      project.code?.toLowerCase().includes(search) ||
      project.client_name?.toLowerCase().includes(search) ||
      project.description?.toLowerCase().includes(search)
    );
  });

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('fr-FR');
  };

  const getBudgetProgress = (project: GryzzlyProject) => {
    if (!project.budget_hours) return null;
    // Ici on pourrait calculer le % en fonction des heures déclarées
    // Pour l'instant on simule
    const used = Math.random() * project.budget_hours;
    const percentage = (used / project.budget_hours) * 100;
    return { used, percentage };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Projets Gryzzly</CardTitle>
        <CardDescription>
          Liste des projets synchronisés depuis Gryzzly
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Rechercher par nom, code, client..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>
          <Button
            variant={activeOnly ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveOnly(!activeOnly)}
          >
            {activeOnly ? 'Actifs' : 'Tous'}
          </Button>
          <Button
            variant={billableOnly ? 'default' : 'outline'}
            size="sm"
            onClick={() => setBillableOnly(!billableOnly)}
          >
            {billableOnly ? 'Facturables' : 'Tous types'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={loadProjects}
          >
            Actualiser
          </Button>
        </div>

        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Statut</TableHead>
                <TableHead>Code</TableHead>
                <TableHead>Nom</TableHead>
                <TableHead>Client</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Facturable</TableHead>
                <TableHead>Budget (h)</TableHead>
                <TableHead>Période</TableHead>
                <TableHead>Dernière sync</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredProjects.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center text-muted-foreground">
                    Aucun projet trouvé
                  </TableCell>
                </TableRow>
              ) : (
                filteredProjects.map((project) => {
                  const budget = getBudgetProgress(project);
                  return (
                    <TableRow key={project.id}>
                      <TableCell>
                        {project.is_active ? (
                          <FolderOpen className="h-4 w-4 text-green-500" />
                        ) : (
                          <FolderOpen className="h-4 w-4 text-gray-400" />
                        )}
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {project.code || '-'}
                      </TableCell>
                      <TableCell className="font-medium">
                        <div>
                          <div>{project.name}</div>
                          {project.description && (
                            <div className="text-xs text-muted-foreground truncate max-w-xs">
                              {project.description}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{project.client_name || '-'}</TableCell>
                      <TableCell>
                        {project.project_type ? (
                          <Badge variant="outline">{project.project_type}</Badge>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell>
                        {project.is_billable ? (
                          <DollarSign className="h-4 w-4 text-green-500" />
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell>
                        {project.budget_hours ? (
                          <div className="space-y-1">
                            <div className="text-sm">{project.budget_hours}h</div>
                            {budget && (
                              <Progress 
                                value={budget.percentage} 
                                className="h-1 w-20"
                              />
                            )}
                          </div>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="text-xs">
                          {project.start_date && (
                            <div>Début: {formatDate(project.start_date)}</div>
                          )}
                          {project.end_date && (
                            <div>Fin: {formatDate(project.end_date)}</div>
                          )}
                          {!project.start_date && !project.end_date && '-'}
                        </div>
                      </TableCell>
                      <TableCell>{formatDate(project.last_synced_at)}</TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>

        <div className="mt-4 text-sm text-muted-foreground">
          {filteredProjects.length} projet(s) sur {projects.length}
        </div>
      </CardContent>
    </Card>
  );
}
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, Search, ListTodo, DollarSign, Clock } from 'lucide-react';
import { toast } from 'sonner';
import gryzzlyService, { GryzzlyTask, GryzzlyProject } from '@/services/gryzzly.service';

export default function GryzzlyTasks() {
  const [tasks, setTasks] = useState<GryzzlyTask[]>([]);
  const [projects, setProjects] = useState<GryzzlyProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProjectId, setSelectedProjectId] = useState<string>('all');
  const [activeOnly, setActiveOnly] = useState(false);

  useEffect(() => {
    loadData();
  }, [selectedProjectId, activeOnly]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load projects for the filter
      const projectsData = await gryzzlyService.getProjects({ limit: 500 });
      setProjects(projectsData);
      
      // Load tasks
      const params: any = {
        active_only: activeOnly,
        limit: 500,
      };
      
      if (selectedProjectId !== 'all') {
        params.project_id = selectedProjectId;
      }
      
      const tasksData = await gryzzlyService.getTasks(params);
      setTasks(tasksData);
    } catch (error) {
      toast.error('Erreur lors du chargement des tâches');
      console.error('Error loading tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredTasks = tasks.filter(task => {
    const search = searchTerm.toLowerCase();
    return (
      task.name?.toLowerCase().includes(search) ||
      task.code?.toLowerCase().includes(search) ||
      task.description?.toLowerCase().includes(search) ||
      task.task_type?.toLowerCase().includes(search)
    );
  });

  const getProjectName = (projectId: string) => {
    const project = projects.find(p => p.id === projectId);
    return project ? project.name : 'Projet inconnu';
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('fr-FR');
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
        <CardTitle>Tâches Gryzzly</CardTitle>
        <CardDescription>
          Liste des tâches synchronisées depuis Gryzzly
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Rechercher par nom, code, type..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>
          <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
            <SelectTrigger className="w-[250px]">
              <SelectValue placeholder="Filtrer par projet" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les projets</SelectItem>
              {projects.map((project) => (
                <SelectItem key={project.id} value={project.id}>
                  {project.code ? `${project.code} - ${project.name}` : project.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant={activeOnly ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveOnly(!activeOnly)}
          >
            {activeOnly ? 'Actives' : 'Toutes'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
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
                <TableHead>Projet</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Facturable</TableHead>
                <TableHead>Heures estimées</TableHead>
                <TableHead>Dernière sync</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTasks.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center text-muted-foreground">
                    Aucune tâche trouvée
                  </TableCell>
                </TableRow>
              ) : (
                filteredTasks.map((task) => (
                  <TableRow key={task.id}>
                    <TableCell>
                      {task.is_active ? (
                        <ListTodo className="h-4 w-4 text-green-500" />
                      ) : (
                        <ListTodo className="h-4 w-4 text-gray-400" />
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {task.code || '-'}
                    </TableCell>
                    <TableCell className="font-medium">
                      <div>
                        <div>{task.name}</div>
                        {task.description && (
                          <div className="text-xs text-muted-foreground truncate max-w-xs">
                            {task.description}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {getProjectName(task.project_id)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {task.task_type ? (
                        <Badge variant="secondary">{task.task_type}</Badge>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      {task.is_billable ? (
                        <DollarSign className="h-4 w-4 text-green-500" />
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      {task.estimated_hours ? (
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3 text-muted-foreground" />
                          <span>{task.estimated_hours}h</span>
                        </div>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>{formatDate(task.last_synced_at)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        <div className="mt-4 text-sm text-muted-foreground">
          {filteredTasks.length} tâche(s) sur {tasks.length}
        </div>
      </CardContent>
    </Card>
  );
}
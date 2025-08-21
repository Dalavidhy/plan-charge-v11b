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
import { Calendar } from '@/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { 
  Loader2, 
  Search, 
  Clock, 
  CalendarIcon,
  CheckCircle,
  XCircle,
  AlertCircle,
  DollarSign
} from 'lucide-react';
import { toast } from 'sonner';
import { logger } from '@/utils/logger';
import gryzzlyService, { 
  GryzzlyDeclaration, 
  GryzzlyCollaborator, 
  GryzzlyProject 
} from '@/services/gryzzly.service';

export default function GryzzlyDeclarations() {
  const [declarations, setDeclarations] = useState<GryzzlyDeclaration[]>([]);
  const [collaborators, setCollaborators] = useState<GryzzlyCollaborator[]>([]);
  const [projects, setProjects] = useState<GryzzlyProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCollaboratorId, setSelectedCollaboratorId] = useState<string>('all');
  const [selectedProjectId, setSelectedProjectId] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [startDate, setStartDate] = useState<Date>();
  const [endDate, setEndDate] = useState<Date>();

  useEffect(() => {
    loadData();
  }, [selectedCollaboratorId, selectedProjectId, selectedStatus, startDate, endDate]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load collaborators and projects for filters
      const [collaboratorsData, projectsData] = await Promise.all([
        gryzzlyService.getCollaborators({ limit: 500 }),
        gryzzlyService.getProjects({ limit: 500 })
      ]);
      setCollaborators(collaboratorsData);
      setProjects(projectsData);
      
      // Load declarations
      const params: any = {
        limit: 500,
      };
      
      if (selectedCollaboratorId !== 'all') {
        params.collaborator_id = selectedCollaboratorId;
      }
      
      if (selectedProjectId !== 'all') {
        params.project_id = selectedProjectId;
      }
      
      if (selectedStatus !== 'all') {
        params.status = selectedStatus;
      }
      
      if (startDate) {
        params.start_date = format(startDate, 'yyyy-MM-dd');
      }
      
      if (endDate) {
        params.end_date = format(endDate, 'yyyy-MM-dd');
      }
      
      const declarationsData = await gryzzlyService.getDeclarations(params);
      setDeclarations(declarationsData);
    } catch (error) {
      toast.error('Erreur lors du chargement des déclarations');
      logger.error('Error loading declarations:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredDeclarations = declarations.filter(declaration => {
    const search = searchTerm.toLowerCase();
    return (
      declaration.description?.toLowerCase().includes(search) ||
      declaration.comment?.toLowerCase().includes(search)
    );
  });

  const getCollaboratorName = (collaboratorId: string) => {
    const collaborator = collaborators.find(c => c.id === collaboratorId);
    return collaborator 
      ? `${collaborator.first_name} ${collaborator.last_name}`.trim() || collaborator.email
      : 'Collaborateur inconnu';
  };

  const getProjectName = (projectId: string) => {
    const project = projects.find(p => p.id === projectId);
    return project ? project.name : 'Projet inconnu';
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('fr-FR');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'rejected':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'submitted':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'draft':
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, any> = {
      'approved': 'secondary',
      'rejected': 'destructive',
      'submitted': 'outline',
      'draft': 'default'
    };
    
    const labels: Record<string, string> = {
      'approved': 'Approuvé',
      'rejected': 'Rejeté',
      'submitted': 'Soumis',
      'draft': 'Brouillon'
    };
    
    return (
      <Badge variant={variants[status] || 'default'}>
        {labels[status] || status}
      </Badge>
    );
  };

  const calculateTotalHours = () => {
    return filteredDeclarations.reduce((total, decl) => total + (decl.duration_hours || 0), 0);
  };

  const calculateTotalCost = () => {
    return filteredDeclarations.reduce((total, decl) => {
      const hours = decl.duration_hours || 0;
      const rate = decl.billing_rate || 0;
      return total + (hours * rate);
    }, 0);
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
        <CardTitle>Déclarations de temps Gryzzly</CardTitle>
        <CardDescription>
          Liste des déclarations de temps synchronisées depuis Gryzzly
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="relative col-span-2">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Rechercher dans les descriptions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>
          
          <Select value={selectedCollaboratorId} onValueChange={setSelectedCollaboratorId}>
            <SelectTrigger>
              <SelectValue placeholder="Tous les collaborateurs" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les collaborateurs</SelectItem>
              {collaborators.map((collab) => (
                <SelectItem key={collab.id} value={collab.id}>
                  {`${collab.first_name} ${collab.last_name}`.trim() || collab.email}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
            <SelectTrigger>
              <SelectValue placeholder="Tous les projets" />
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
          
          <Select value={selectedStatus} onValueChange={setSelectedStatus}>
            <SelectTrigger>
              <SelectValue placeholder="Tous les statuts" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les statuts</SelectItem>
              <SelectItem value="draft">Brouillon</SelectItem>
              <SelectItem value="submitted">Soumis</SelectItem>
              <SelectItem value="approved">Approuvé</SelectItem>
              <SelectItem value="rejected">Rejeté</SelectItem>
            </SelectContent>
          </Select>
          
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className={cn(
                  "justify-start text-left font-normal",
                  !startDate && "text-muted-foreground"
                )}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {startDate ? format(startDate, "dd/MM/yyyy", { locale: fr }) : "Date début"}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="single"
                selected={startDate}
                onSelect={setStartDate}
                initialFocus
              />
            </PopoverContent>
          </Popover>
          
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className={cn(
                  "justify-start text-left font-normal",
                  !endDate && "text-muted-foreground"
                )}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {endDate ? format(endDate, "dd/MM/yyyy", { locale: fr }) : "Date fin"}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="single"
                selected={endDate}
                onSelect={setEndDate}
                initialFocus
              />
            </PopoverContent>
          </Popover>
          
          <Button
            variant="outline"
            onClick={loadData}
          >
            Actualiser
          </Button>
        </div>

        <div className="flex gap-4 mb-4">
          <Card className="flex-1">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{calculateTotalHours().toFixed(2)}h</div>
              <p className="text-xs text-muted-foreground">Total heures</p>
            </CardContent>
          </Card>
          <Card className="flex-1">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{(calculateTotalHours() / 7).toFixed(2)}j</div>
              <p className="text-xs text-muted-foreground">Total jours</p>
            </CardContent>
          </Card>
          <Card className="flex-1">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{calculateTotalCost().toFixed(2)}€</div>
              <p className="text-xs text-muted-foreground">Montant facturable</p>
            </CardContent>
          </Card>
        </div>

        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Collaborateur</TableHead>
                <TableHead>Projet</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Durée</TableHead>
                <TableHead>Facturable</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead>Approuvé par</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDeclarations.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center text-muted-foreground">
                    Aucune déclaration trouvée
                  </TableCell>
                </TableRow>
              ) : (
                filteredDeclarations.map((declaration) => (
                  <TableRow key={declaration.id}>
                    <TableCell>{formatDate(declaration.date)}</TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {getCollaboratorName(declaration.collaborator_id)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {getProjectName(declaration.project_id)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="text-sm">{declaration.description || '-'}</div>
                        {declaration.comment && (
                          <div className="text-xs text-muted-foreground">
                            {declaration.comment}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3 text-muted-foreground" />
                        <span>
                          {declaration.duration_hours}h
                          {declaration.duration_minutes ? ` ${declaration.duration_minutes}m` : ''}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {declaration.is_billable ? (
                        <DollarSign className="h-4 w-4 text-green-500" />
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(declaration.status)}
                        {getStatusBadge(declaration.status)}
                      </div>
                    </TableCell>
                    <TableCell>
                      {declaration.approved_by || '-'}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        <div className="mt-4 text-sm text-muted-foreground">
          {filteredDeclarations.length} déclaration(s) sur {declarations.length}
        </div>
      </CardContent>
    </Card>
  );
}
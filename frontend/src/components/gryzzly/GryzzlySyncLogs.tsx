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
import {
  Loader2,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  RefreshCw,
  Users,
  FolderOpen,
  ListTodo,
  FileText
} from 'lucide-react';
import { toast } from 'sonner';
import gryzzlyService, { GryzzlySyncLog } from '@/services/gryzzly.service';
import { logger } from '@/utils/logger';

export default function GryzzlySyncLogs() {
  const [syncLogs, setSyncLogs] = useState<GryzzlySyncLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');

  useEffect(() => {
    loadSyncLogs();
  }, [selectedType, selectedStatus]);

  const loadSyncLogs = async () => {
    try {
      setLoading(true);
      const params: any = {
        limit: 100,
      };

      if (selectedType !== 'all') {
        params.sync_type = selectedType;
      }

      if (selectedStatus !== 'all') {
        params.status = selectedStatus;
      }

      const data = await gryzzlyService.getSyncLogs(params);
      setSyncLogs(data);
    } catch (error) {
      toast.error('Erreur lors du chargement des logs de synchronisation');
      logger.error('Error loading sync logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'in_progress':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, any> = {
      'success': 'secondary',
      'error': 'destructive',
      'in_progress': 'outline',
      'pending': 'default'
    };

    const labels: Record<string, string> = {
      'success': 'Succès',
      'error': 'Erreur',
      'in_progress': 'En cours',
      'pending': 'En attente'
    };

    return (
      <Badge variant={variants[status] || 'default'}>
        {labels[status] || status}
      </Badge>
    );
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'collaborators':
        return <Users className="h-4 w-4 text-blue-500" />;
      case 'projects':
        return <FolderOpen className="h-4 w-4 text-purple-500" />;
      case 'tasks':
        return <ListTodo className="h-4 w-4 text-orange-500" />;
      case 'declarations':
        return <FileText className="h-4 w-4 text-green-500" />;
      case 'full':
        return <RefreshCw className="h-4 w-4 text-indigo-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTypeBadge = (type: string) => {
    const labels: Record<string, string> = {
      'collaborators': 'Collaborateurs',
      'projects': 'Projets',
      'tasks': 'Tâches',
      'declarations': 'Déclarations',
      'full': 'Complète'
    };

    return (
      <div className="flex items-center gap-1">
        {getTypeIcon(type)}
        <span>{labels[type] || type}</span>
      </div>
    );
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes < 60) return `${minutes}m ${remainingSeconds}s`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const successRate = syncLogs.length > 0
    ? Math.round((syncLogs.filter(log => log.sync_status === 'success').length / syncLogs.length) * 100)
    : 0;

  const totalRecordsSynced = syncLogs.reduce((total, log) => total + log.records_synced, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Historique des synchronisations Gryzzly</CardTitle>
        <CardDescription>
          Liste des synchronisations effectuées avec Gryzzly
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{syncLogs.length}</div>
              <p className="text-xs text-muted-foreground">Total synchronisations</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{successRate}%</div>
              <p className="text-xs text-muted-foreground">Taux de succès</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{totalRecordsSynced}</div>
              <p className="text-xs text-muted-foreground">Enregistrements synchronisés</p>
            </CardContent>
          </Card>
        </div>

        <div className="flex items-center gap-4 mb-4">
          <Select value={selectedType} onValueChange={setSelectedType}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Tous les types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les types</SelectItem>
              <SelectItem value="collaborators">Collaborateurs</SelectItem>
              <SelectItem value="projects">Projets</SelectItem>
              <SelectItem value="tasks">Tâches</SelectItem>
              <SelectItem value="declarations">Déclarations</SelectItem>
              <SelectItem value="full">Synchronisation complète</SelectItem>
            </SelectContent>
          </Select>

          <Select value={selectedStatus} onValueChange={setSelectedStatus}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Tous les statuts" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les statuts</SelectItem>
              <SelectItem value="success">Succès</SelectItem>
              <SelectItem value="error">Erreur</SelectItem>
              <SelectItem value="in_progress">En cours</SelectItem>
              <SelectItem value="pending">En attente</SelectItem>
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            size="sm"
            onClick={loadSyncLogs}
          >
            Actualiser
          </Button>
        </div>

        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead>Durée</TableHead>
                <TableHead>Synchronisés</TableHead>
                <TableHead>Créés</TableHead>
                <TableHead>Mis à jour</TableHead>
                <TableHead>Échecs</TableHead>
                <TableHead>Déclenché par</TableHead>
                <TableHead>Message</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {syncLogs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} className="text-center text-muted-foreground">
                    Aucun log de synchronisation trouvé
                  </TableCell>
                </TableRow>
              ) : (
                syncLogs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>
                      <div className="text-xs">
                        {formatDate(log.started_at)}
                      </div>
                    </TableCell>
                    <TableCell>
                      {getTypeBadge(log.sync_type)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(log.sync_status)}
                        {getStatusBadge(log.sync_status)}
                      </div>
                    </TableCell>
                    <TableCell>
                      {formatDuration(log.duration_seconds)}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {log.records_synced}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {log.records_created > 0 ? (
                        <span className="text-green-600">
                          +{log.records_created}
                        </span>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      {log.records_updated > 0 ? (
                        <span className="text-blue-600">
                          {log.records_updated}
                        </span>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      {log.records_failed > 0 ? (
                        <span className="text-red-600">
                          {log.records_failed}
                        </span>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      {log.triggered_by || 'Système'}
                    </TableCell>
                    <TableCell>
                      {log.error_message ? (
                        <span className="text-xs text-red-600" title={log.error_message}>
                          {log.error_message.substring(0, 50)}...
                        </span>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        <div className="mt-4 text-sm text-muted-foreground">
          {syncLogs.length} log(s) de synchronisation
        </div>
      </CardContent>
    </Card>
  );
}

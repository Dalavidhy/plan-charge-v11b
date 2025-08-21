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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Info,
  Activity
} from 'lucide-react';
import payfitService, { PayfitSyncLog } from '@/services/payfit.service';
import { toast } from 'sonner';
import { logger } from '@/utils/logger';

export default function PayfitSyncLogs() {
  const [logs, setLogs] = useState<PayfitSyncLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    loadLogs();
  }, [typeFilter, statusFilter]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const params: any = { limit: 50 };
      if (typeFilter !== 'all') {
        params.sync_type = typeFilter;
      }
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }
      const data = await payfitService.getSyncLogs(params);
      setLogs(data);
    } catch (error) {
      toast.error('Erreur lors du chargement des logs');
      logger.error('Error loading sync logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'started':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'partial':
        return <AlertCircle className="h-4 w-4 text-orange-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'success':
        return 'default';
      case 'failed':
        return 'destructive';
      case 'started':
        return 'outline';
      case 'partial':
        return 'secondary';
      default:
        return 'secondary';
    }
  };

  const getTypeLabel = (type: string) => {
    const typeMap: Record<string, string> = {
      'full': 'Complète',
      'employees': 'Employés',
      'contracts': 'Contrats',
      'absences': 'Absences',
    };
    return typeMap[type] || type;
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Historique de synchronisation</CardTitle>
        <CardDescription>
          Logs des synchronisations Payfit
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="flex items-center gap-4 mb-4">
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Type de sync" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les types</SelectItem>
              <SelectItem value="full">Complète</SelectItem>
              <SelectItem value="employees">Employés</SelectItem>
              <SelectItem value="contracts">Contrats</SelectItem>
              <SelectItem value="absences">Absences</SelectItem>
            </SelectContent>
          </Select>

          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Statut" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les statuts</SelectItem>
              <SelectItem value="success">Succès</SelectItem>
              <SelectItem value="failed">Échec</SelectItem>
              <SelectItem value="started">En cours</SelectItem>
              <SelectItem value="partial">Partiel</SelectItem>
            </SelectContent>
          </Select>

          <Button variant="outline" onClick={loadLogs}>
            Actualiser
          </Button>
        </div>

        {/* Table */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead>Durée</TableHead>
                <TableHead>Enregistrements</TableHead>
                <TableHead>Déclenché par</TableHead>
                <TableHead>Message</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center">
                    Aucun log trouvé
                  </TableCell>
                </TableRow>
              ) : (
                logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="font-medium">
                      {formatDate(log.started_at)}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {getTypeLabel(log.sync_type)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(log.sync_status)}
                        <Badge variant={getStatusVariant(log.sync_status)}>
                          {log.sync_status === 'success' && 'Succès'}
                          {log.sync_status === 'failed' && 'Échec'}
                          {log.sync_status === 'started' && 'En cours'}
                          {log.sync_status === 'partial' && 'Partiel'}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>{formatDuration(log.duration_seconds)}</TableCell>
                    <TableCell>
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger>
                            <div className="flex items-center gap-1">
                              <Activity className="h-4 w-4" />
                              <span>{log.records_synced}</span>
                            </div>
                          </TooltipTrigger>
                          <TooltipContent>
                            <div className="text-xs">
                              <p>Créés: {log.records_created}</p>
                              <p>Mis à jour: {log.records_updated}</p>
                              <p>Échoués: {log.records_failed}</p>
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </TableCell>
                    <TableCell>{log.triggered_by || 'Système'}</TableCell>
                    <TableCell className="max-w-xs">
                      {log.error_message ? (
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger>
                              <span className="text-red-500 truncate block">
                                {log.error_message}
                              </span>
                            </TooltipTrigger>
                            <TooltipContent className="max-w-sm">
                              <p className="text-xs">{log.error_message}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      ) : (
                        <span className="text-green-500">✓</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Summary */}
        <div className="mt-4 text-sm text-muted-foreground">
          {logs.length} log(s) trouvé(s)
        </div>
      </CardContent>
    </Card>
  );
}

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Loader2,
  Users,
  Calendar,
  FileText,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  XCircle,
  Clock,
  Activity,
  Link,
  Unlink,
} from 'lucide-react';
import { toast } from 'sonner';
import payfitService, {
  PayfitStats,
  PayfitSyncStatus,
  PayfitEmployee,
  PayfitContract,
  PayfitAbsence,
  PayfitSyncLog,
} from '@/services/payfit.service';

// Import child components
import PayfitEmployees from '@/components/payfit/PayfitEmployees';
import PayfitAbsences from '@/components/payfit/PayfitAbsences';
import PayfitContracts from '@/components/payfit/PayfitContracts';
import PayfitSyncLogs from '@/components/payfit/PayfitSyncLogs';
import { logger } from '@/utils/logger';

export default function PayfitDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [stats, setStats] = useState<PayfitStats | null>(null);
  const [syncStatus, setSyncStatus] = useState<PayfitSyncStatus | null>(null);
  const [connectionTested, setConnectionTested] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      logger.debug('📊 PayfitDashboard: Loading data...');
      const [statsData, statusData] = await Promise.all([
        payfitService.getStats(),
        payfitService.getStatus(),
      ]);
      setStats(statsData);
      setSyncStatus(statusData);
      logger.debug('✅ PayfitDashboard: Data loaded successfully', { statsData, statusData });
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || 
                          error?.response?.data?.message || 
                          error?.message ||
                          'Erreur lors du chargement des données Payfit';
      toast.error(errorMessage);
      logger.error('❌ PayfitDashboard: Error loading data:', error);
      logger.error('📋 Error details:', {
        status: error?.response?.status,
        statusText: error?.response?.statusText,
        data: error?.response?.data,
        message: error?.message
      });
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async () => {
    try {
      setConnectionTested(false);
      const result = await payfitService.testConnection();
      setConnectionTested(true);
      toast.success(result.message);
      await loadData();
    } catch (error) {
      toast.error('Impossible de se connecter à l\'API Payfit');
      logger.error('Connection test failed:', error);
    }
  };

  const handleSync = async (type: 'employees' | 'contracts' | 'absences' | 'full') => {
    try {
      setSyncing(true);
      let result;
      
      switch (type) {
        case 'employees':
          result = await payfitService.syncEmployees();
          break;
        case 'contracts':
          result = await payfitService.syncContracts();
          break;
        case 'absences':
          result = await payfitService.syncAbsences();
          break;
        case 'full':
          result = await payfitService.syncFull();
          break;
      }
      
      toast.success(result.message);
      
      // Reload data after a delay to allow sync to complete
      setTimeout(() => {
        loadData();
      }, 3000);
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || 
                          error?.response?.data?.message || 
                          error?.message ||
                          `Erreur lors de la synchronisation ${type}`;
      toast.error(errorMessage);
      logger.error(`Sync ${type} failed:`, error);
    } finally {
      setSyncing(false);
    }
  };

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getSyncStatusIcon = (status?: string | null) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'started':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getSyncStatusColor = (status?: string | null): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'success':
        return 'secondary';
      case 'failed':
        return 'destructive';
      case 'started':
        return 'outline';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Synchronisation Payfit</h1>
          <p className="text-muted-foreground">
            Gérez la synchronisation des données depuis Payfit
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={testConnection}
            disabled={syncing}
          >
            {connectionTested ? (
              <Link className="h-4 w-4 mr-2" />
            ) : (
              <Unlink className="h-4 w-4 mr-2" />
            )}
            Tester la connexion
          </Button>
          <Button
            variant="outline"
            onClick={loadData}
            disabled={syncing}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualiser
          </Button>
          <Button
            onClick={() => handleSync('full')}
            disabled={syncing}
          >
            {syncing ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Activity className="h-4 w-4 mr-2" />
            )}
            Synchronisation complète
          </Button>
        </div>
      </div>

      {/* Connection Status */}
      {syncStatus && (
        <Alert variant={syncStatus.api_connected ? 'default' : 'destructive'}>
          <AlertTitle>
            État de la connexion
          </AlertTitle>
          <AlertDescription className="flex items-center gap-2">
            {syncStatus.api_connected ? (
              <>
                <CheckCircle className="h-4 w-4 text-green-500" />
                API Payfit connectée
              </>
            ) : (
              <>
                <XCircle className="h-4 w-4 text-red-500" />
                API Payfit non connectée
              </>
            )}
            {syncStatus.last_sync && syncStatus.last_sync.timestamp && (
              <span className="ml-4">
                Dernière sync: {formatDate(syncStatus.last_sync.timestamp)}
              </span>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Statistics Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Employés</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_employees || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.active_employees || 0} actifs
            </p>
            <Button
              size="sm"
              variant="ghost"
              className="mt-2 w-full"
              onClick={() => handleSync('employees')}
              disabled={syncing}
            >
              Synchroniser
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Contrats</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_contracts || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.active_contracts || 0} actifs
            </p>
            <Button
              size="sm"
              variant="ghost"
              className="mt-2 w-full"
              onClick={() => handleSync('contracts')}
              disabled={syncing}
            >
              Synchroniser
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Absences</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_absences || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.approved_absences || 0} approuvées, {stats?.pending_absences || 0} en attente
            </p>
            <Button
              size="sm"
              variant="ghost"
              className="mt-2 w-full"
              onClick={() => handleSync('absences')}
              disabled={syncing}
            >
              Synchroniser
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Dernière sync</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {getSyncStatusIcon(syncStatus?.last_sync?.status)}
              <Badge variant={getSyncStatusColor(syncStatus?.last_sync?.status)}>
                {syncStatus?.last_sync?.status || 'Jamais'}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {syncStatus?.last_sync?.type && `Type: ${syncStatus.last_sync.type}`}
            </p>
            {syncStatus?.last_sync?.records_synced !== undefined && (
              <p className="text-xs text-muted-foreground">
                {syncStatus.last_sync.records_synced} enregistrements
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Vue d'ensemble</TabsTrigger>
          <TabsTrigger value="employees">Employés</TabsTrigger>
          <TabsTrigger value="contracts">Contrats</TabsTrigger>
          <TabsTrigger value="absences">Absences</TabsTrigger>
          <TabsTrigger value="logs">Historique</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <Card>
            <CardHeader>
              <CardTitle>Vue d'ensemble de la synchronisation</CardTitle>
              <CardDescription>
                État actuel et statistiques de synchronisation Payfit
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium mb-2">Données synchronisées</h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Employés</span>
                      <span className="text-sm font-medium">
                        {syncStatus?.data_counts?.employees || 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Contrats</span>
                      <span className="text-sm font-medium">
                        {syncStatus?.data_counts?.contracts || 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Absences</span>
                      <span className="text-sm font-medium">
                        {syncStatus?.data_counts?.absences || 0}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="employees">
          <PayfitEmployees />
        </TabsContent>

        <TabsContent value="contracts">
          <PayfitContracts />
        </TabsContent>

        <TabsContent value="absences">
          <PayfitAbsences />
        </TabsContent>

        <TabsContent value="logs">
          <PayfitSyncLogs />
        </TabsContent>
      </Tabs>
    </div>
  );
}
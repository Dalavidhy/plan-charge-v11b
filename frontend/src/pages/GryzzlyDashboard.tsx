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
import {
  Loader2,
  Users,
  Briefcase,
  ListTodo,
  Clock,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  XCircle,
  Activity,
  Link,
  Unlink,
  FolderOpen,
  DollarSign,
} from 'lucide-react';
import { toast } from 'sonner';
import gryzzlyService, {
  GryzzlyStats,
  GryzzlySyncStatus,
} from '@/services/gryzzly.service';

// Import child components
import GryzzlyCollaborators from '@/components/gryzzly/GryzzlyCollaborators';
import GryzzlyProjects from '@/components/gryzzly/GryzzlyProjects';
import GryzzlyTasks from '@/components/gryzzly/GryzzlyTasks';
import GryzzlyDeclarations from '@/components/gryzzly/GryzzlyDeclarations';
import GryzzlySyncLogs from '@/components/gryzzly/GryzzlySyncLogs';
import { logger } from '@/utils/logger';

export default function GryzzlyDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [stats, setStats] = useState<GryzzlyStats | null>(null);
  const [syncStatus, setSyncStatus] = useState<GryzzlySyncStatus | null>(null);
  const [connectionTested, setConnectionTested] = useState(false);
  const [isMockMode] = useState(import.meta.env.VITE_GRYZZLY_USE_MOCK === 'true');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      logger.debug('📊 GryzzlyDashboard: Loading data...');
      const [statsData, statusData] = await Promise.all([
        gryzzlyService.getStats(),
        gryzzlyService.getStatus(),
      ]);
      setStats(statsData);
      setSyncStatus(statusData);
      logger.debug('✅ GryzzlyDashboard: Data loaded successfully', { statsData, statusData });
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || 
                          error?.response?.data?.message || 
                          error?.message ||
                          'Erreur lors du chargement des données Gryzzly';
      toast.error(errorMessage);
      logger.error('❌ GryzzlyDashboard: Error loading data:', error);
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
      const result = await gryzzlyService.testConnection();
      setConnectionTested(true);
      toast.success(result.message);
      await loadData();
    } catch (error) {
      toast.error('Impossible de se connecter à l\'API Gryzzly');
      logger.error('Connection test failed:', error);
    }
  };

  const handleSync = async (type: 'collaborators' | 'projects' | 'tasks' | 'declarations' | 'full') => {
    try {
      setSyncing(true);
      let result;
      
      switch (type) {
        case 'collaborators':
          result = await gryzzlyService.syncCollaborators();
          break;
        case 'projects':
          result = await gryzzlyService.syncProjects();
          break;
        case 'tasks':
          result = await gryzzlyService.syncTasks();
          break;
        case 'declarations':
          result = await gryzzlyService.syncDeclarations();
          break;
        case 'full':
          result = await gryzzlyService.syncFull();
          break;
      }
      
      toast.success(result.message);
      
      // Reload data after a delay to allow sync to complete
      setTimeout(() => {
        loadData();
      }, 3000);
    } catch (error) {
      toast.error(`Erreur lors de la synchronisation ${type}`);
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
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-3xl font-bold">Synchronisation Gryzzly</h1>
            <p className="text-muted-foreground">
              Gérez la synchronisation des données depuis Gryzzly
            </p>
          </div>
          {isMockMode && (
            <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-300">
              Mode Démo
            </Badge>
          )}
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
            {isMockMode && (
              <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-300 mr-2">
                Mode Démo Actif
              </Badge>
            )}
            {syncStatus.api_connected ? (
              <>
                <CheckCircle className="h-4 w-4 text-green-500" />
                API Gryzzly connectée
              </>
            ) : (
              <>
                <XCircle className="h-4 w-4 text-red-500" />
                API Gryzzly non connectée
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
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Collaborateurs</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_collaborators || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.active_collaborators || 0} actifs
            </p>
            <Button
              size="sm"
              variant="ghost"
              className="mt-2 w-full"
              onClick={() => handleSync('collaborators')}
              disabled={syncing}
            >
              Synchroniser
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Projets</CardTitle>
            <FolderOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_projects || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.active_projects || 0} actifs, {stats?.billable_projects || 0} facturables
            </p>
            <Button
              size="sm"
              variant="ghost"
              className="mt-2 w-full"
              onClick={() => handleSync('projects')}
              disabled={syncing}
            >
              Synchroniser
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tâches</CardTitle>
            <ListTodo className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_tasks || 0}</div>
            <p className="text-xs text-muted-foreground">
              Tâches définies
            </p>
            <Button
              size="sm"
              variant="ghost"
              className="mt-2 w-full"
              onClick={() => handleSync('tasks')}
              disabled={syncing}
            >
              Synchroniser
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Déclarations</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_declarations || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.approved_declarations || 0} approuvées, {stats?.pending_declarations || 0} en attente
            </p>
            <Button
              size="sm"
              variant="ghost"
              className="mt-2 w-full"
              onClick={() => handleSync('declarations')}
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
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Vue d'ensemble</TabsTrigger>
          <TabsTrigger value="collaborators">Collaborateurs</TabsTrigger>
          <TabsTrigger value="projects">Projets</TabsTrigger>
          <TabsTrigger value="tasks">Tâches</TabsTrigger>
          <TabsTrigger value="declarations">Déclarations</TabsTrigger>
          <TabsTrigger value="logs">Historique</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <Card>
            <CardHeader>
              <CardTitle>Vue d'ensemble de la synchronisation</CardTitle>
              <CardDescription>
                État actuel et statistiques de synchronisation Gryzzly
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium mb-2">Données synchronisées</h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Collaborateurs</span>
                      <span className="text-sm font-medium">
                        {syncStatus?.data_counts?.collaborators || 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Projets</span>
                      <span className="text-sm font-medium">
                        {syncStatus?.data_counts?.projects || 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Tâches</span>
                      <span className="text-sm font-medium">
                        {syncStatus?.data_counts?.tasks || 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Déclarations</span>
                      <span className="text-sm font-medium">
                        {syncStatus?.data_counts?.declarations || 0}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="collaborators">
          <GryzzlyCollaborators />
        </TabsContent>

        <TabsContent value="projects">
          <GryzzlyProjects />
        </TabsContent>

        <TabsContent value="tasks">
          <GryzzlyTasks />
        </TabsContent>

        <TabsContent value="declarations">
          <GryzzlyDeclarations />
        </TabsContent>

        <TabsContent value="logs">
          <GryzzlySyncLogs />
        </TabsContent>
      </Tabs>
    </div>
  );
}
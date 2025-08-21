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
import { Loader2, Search, User, UserCheck, UserX } from 'lucide-react';
import { toast } from 'sonner';
import gryzzlyService, { GryzzlyCollaborator } from '@/services/gryzzly.service';
import { logger } from '@/utils/logger';

export default function GryzzlyCollaborators() {
  const [collaborators, setCollaborators] = useState<GryzzlyCollaborator[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeOnly, setActiveOnly] = useState(false);

  useEffect(() => {
    loadCollaborators();
  }, [activeOnly]);

  const loadCollaborators = async () => {
    try {
      setLoading(true);
      const data = await gryzzlyService.getCollaborators({
        active_only: activeOnly,
        limit: 500,
      });
      setCollaborators(data);
    } catch (error) {
      toast.error('Erreur lors du chargement des collaborateurs');
      logger.error('Error loading collaborators:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCollaborators = collaborators.filter(collab => {
    const search = searchTerm.toLowerCase();
    return (
      collab.email?.toLowerCase().includes(search) ||
      collab.first_name?.toLowerCase().includes(search) ||
      collab.last_name?.toLowerCase().includes(search) ||
      collab.matricule?.toLowerCase().includes(search) ||
      collab.department?.toLowerCase().includes(search) ||
      collab.position?.toLowerCase().includes(search)
    );
  });

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
        <CardTitle>Collaborateurs Gryzzly</CardTitle>
        <CardDescription>
          Liste des collaborateurs synchronisés depuis Gryzzly
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Rechercher par nom, email, matricule..."
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
            {activeOnly ? 'Actifs uniquement' : 'Tous'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={loadCollaborators}
          >
            Actualiser
          </Button>
        </div>

        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Statut</TableHead>
                <TableHead>Nom</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Matricule</TableHead>
                <TableHead>Département</TableHead>
                <TableHead>Poste</TableHead>
                <TableHead>Admin</TableHead>
                <TableHead>Lié</TableHead>
                <TableHead>Dernière sync</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCollaborators.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center text-muted-foreground">
                    Aucun collaborateur trouvé
                  </TableCell>
                </TableRow>
              ) : (
                filteredCollaborators.map((collab) => (
                  <TableRow key={collab.id}>
                    <TableCell>
                      {collab.is_active ? (
                        <UserCheck className="h-4 w-4 text-green-500" />
                      ) : (
                        <UserX className="h-4 w-4 text-gray-400" />
                      )}
                    </TableCell>
                    <TableCell className="font-medium">
                      {collab.first_name} {collab.last_name}
                    </TableCell>
                    <TableCell>{collab.email}</TableCell>
                    <TableCell>{collab.matricule || '-'}</TableCell>
                    <TableCell>{collab.department || '-'}</TableCell>
                    <TableCell>{collab.position || '-'}</TableCell>
                    <TableCell>
                      {collab.is_admin ? (
                        <Badge variant="secondary">Admin</Badge>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      {collab.local_user_id ? (
                        <User className="h-4 w-4 text-blue-500" />
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>{formatDate(collab.last_synced_at)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        <div className="mt-4 text-sm text-muted-foreground">
          {filteredCollaborators.length} collaborateur(s) sur {collaborators.length}
        </div>
      </CardContent>
    </Card>
  );
}

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2, Calendar, CheckCircle, XCircle, Clock } from 'lucide-react';
import payfitService, { PayfitAbsence } from '@/services/payfit.service';
import { toast } from 'sonner';
import { logger } from '@/utils/logger';

export default function PayfitAbsences() {
  const [absences, setAbsences] = useState<PayfitAbsence[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  useEffect(() => {
    loadAbsences();
  }, [statusFilter]);

  const loadAbsences = async () => {
    try {
      setLoading(true);
      const params: any = { limit: 100 };
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }
      const data = await payfitService.getAbsences(params);
      setAbsences(data);
    } catch (error) {
      toast.error('Erreur lors du chargement des absences');
      logger.error('Error loading absences:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredAbsences = absences.filter((absence) => {
    if (typeFilter === 'all') return true;
    return absence.absence_type === typeFilter;
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'rejected':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return null;
    }
  };

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'approved':
        return 'default';
      case 'rejected':
        return 'destructive';
      case 'pending':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  const getAbsenceTypeLabel = (type: string) => {
    const typeMap: Record<string, string> = {
      'vacation': 'Congés payés',
      'sick_leave': 'Arrêt maladie',
      'unpaid_leave': 'Congé sans solde',
      'maternity': 'Congé maternité',
      'paternity': 'Congé paternité',
      'family_event': 'Événement familial',
      'training': 'Formation',
      'other': 'Autre',
    };
    return typeMap[type] || type;
  };

  // Get unique absence types for filter
  const absenceTypes = Array.from(new Set(absences.map(a => a.absence_type)));

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
        <CardTitle>Absences Payfit</CardTitle>
        <CardDescription>
          Liste des absences synchronisées depuis Payfit
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="flex items-center gap-4 mb-4">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Statut" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les statuts</SelectItem>
              <SelectItem value="approved">Approuvées</SelectItem>
              <SelectItem value="pending">En attente</SelectItem>
              <SelectItem value="rejected">Rejetées</SelectItem>
              <SelectItem value="cancelled">Annulées</SelectItem>
            </SelectContent>
          </Select>

          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Type d'absence" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les types</SelectItem>
              {absenceTypes.map((type) => (
                <SelectItem key={type} value={type}>
                  {getAbsenceTypeLabel(type)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button variant="outline" onClick={loadAbsences}>
            Actualiser
          </Button>
        </div>

        {/* Table */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Employé</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Date début</TableHead>
                <TableHead>Date fin</TableHead>
                <TableHead>Durée</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead>Commentaire</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAbsences.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center">
                    Aucune absence trouvée
                  </TableCell>
                </TableRow>
              ) : (
                filteredAbsences.map((absence) => (
                  <TableRow key={absence.id}>
                    <TableCell className="font-medium">
                      {absence.employee_full_name || absence.employee_email || absence.payfit_employee_id}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {getAbsenceTypeLabel(absence.absence_type)}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatDate(absence.start_date)}</TableCell>
                    <TableCell>{formatDate(absence.end_date)}</TableCell>
                    <TableCell>
                      {absence.duration_days ? `${absence.duration_days} jour(s)` : 'N/A'}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(absence.status)}
                        <Badge variant={getStatusVariant(absence.status)}>
                          {absence.status === 'approved' && 'Approuvée'}
                          {absence.status === 'pending' && 'En attente'}
                          {absence.status === 'rejected' && 'Rejetée'}
                          {absence.status === 'cancelled' && 'Annulée'}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell className="max-w-xs truncate">
                      {absence.comment || '-'}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Summary */}
        <div className="mt-4 text-sm text-muted-foreground">
          {filteredAbsences.length} absence(s) sur {absences.length} total
        </div>
      </CardContent>
    </Card>
  );
}

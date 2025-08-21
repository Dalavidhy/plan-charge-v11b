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
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import { Loader2, FileText, Clock } from 'lucide-react';
import payfitService, { PayfitContract } from '@/services/payfit.service';
import { toast } from 'sonner';
import { logger } from '@/utils/logger';

export default function PayfitContracts() {
  const [contracts, setContracts] = useState<PayfitContract[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeOnly, setActiveOnly] = useState(false);

  useEffect(() => {
    loadContracts();
  }, [activeOnly]);

  const loadContracts = async () => {
    try {
      setLoading(true);
      const data = await payfitService.getContracts({
        active_only: activeOnly,
        limit: 100,
      });
      setContracts(data);
    } catch (error) {
      toast.error('Erreur lors du chargement des contrats');
      logger.error('Error loading contracts:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('fr-FR');
  };

  const getContractTypeLabel = (type?: string) => {
    const typeMap: Record<string, string> = {
      'CDI': 'CDI',
      'CDD': 'CDD',
      'apprenticeship': 'Apprentissage',
      'internship': 'Stage',
      'freelance': 'Freelance',
      'temporary': 'Intérim',
    };
    return typeMap[type || ''] || type || 'Non défini';
  };

  const getContractTypeVariant = (type?: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (type) {
      case 'CDI':
        return 'default';
      case 'CDD':
        return 'secondary';
      case 'apprenticeship':
      case 'internship':
        return 'outline';
      default:
        return 'secondary';
    }
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
        <CardTitle>Contrats Payfit</CardTitle>
        <CardDescription>
          Liste des contrats synchronisés depuis Payfit
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="flex items-center gap-4 mb-4">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="active-contracts-only"
              checked={activeOnly}
              onCheckedChange={(checked) => setActiveOnly(checked as boolean)}
            />
            <label
              htmlFor="active-contracts-only"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              Contrats actifs uniquement
            </label>
          </div>
          <Button variant="outline" onClick={loadContracts}>
            Actualiser
          </Button>
        </div>

        {/* Statistics */}
        <div className="grid gap-4 md:grid-cols-3 mb-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total contrats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{contracts.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Contrats actifs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {contracts.filter(c => c.is_active).length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Temps plein</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {contracts.filter(c => c.part_time_percentage === 100 || c.part_time_percentage === undefined).length}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Table */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Employé</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Poste</TableHead>
                <TableHead>Date début</TableHead>
                <TableHead>Date fin</TableHead>
                <TableHead>Temps de travail</TableHead>
                <TableHead>Statut</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {contracts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center">
                    Aucun contrat trouvé
                  </TableCell>
                </TableRow>
              ) : (
                contracts.map((contract) => (
                  <TableRow key={contract.id}>
                    <TableCell className="font-medium">
                      {contract.employee_full_name || contract.employee_email || contract.payfit_employee_id}
                    </TableCell>
                    <TableCell>
                      <Badge variant={getContractTypeVariant(contract.contract_type)}>
                        {getContractTypeLabel(contract.contract_type)}
                      </Badge>
                    </TableCell>
                    <TableCell>{contract.job_title || 'N/A'}</TableCell>
                    <TableCell>{formatDate(contract.start_date)}</TableCell>
                    <TableCell>
                      {contract.end_date ? formatDate(contract.end_date) : '-'}
                    </TableCell>
                    <TableCell>
                      {contract.weekly_hours ? (
                        <div className="flex items-center gap-2">
                          <span className="text-sm">{contract.weekly_hours}h/sem</span>
                          {contract.part_time_percentage && contract.part_time_percentage < 100 && (
                            <Badge variant="outline" className="text-xs">
                              {contract.part_time_percentage}%
                            </Badge>
                          )}
                        </div>
                      ) : (
                        'N/A'
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant={contract.is_active ? 'default' : 'secondary'}>
                        {contract.is_active ? 'Actif' : 'Terminé'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Summary */}
        <div className="mt-4 text-sm text-muted-foreground">
          {contracts.length} contrat(s) trouvé(s)
        </div>
      </CardContent>
    </Card>
  );
}

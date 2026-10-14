import type { Employee } from '@/types/auth.types';
import { RequesterInfoCard } from './RequesterInfoCard';

interface RequisitionRequesterSummaryProps {
  employee: Employee | null;
}

export function RequisitionRequesterSummary({ employee }: RequisitionRequesterSummaryProps) {
  return <RequesterInfoCard employee={employee} />;
}

export default RequisitionRequesterSummary;
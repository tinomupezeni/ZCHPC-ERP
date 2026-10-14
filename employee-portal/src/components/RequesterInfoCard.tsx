import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { UserRound } from 'lucide-react';
import type { Employee } from '@/types/auth.types';

interface RequesterInfoCardProps {
  employee: Employee | null;
}

/**
 * Details of Officer Requesting (read-only).
 * Automatically derived from the authenticated employee's session profile,
 * eliminating manual re-typing of requester credentials.
 */
export function RequesterInfoCard({ employee }: RequesterInfoCardProps) {
  if (!employee) return null;

  const fullName =
    employee.full_name ||
    `${employee.first_name || ''} ${employee.surname || ''}`.trim() ||
    'Not set';

  return (
    <Card className="border border-border/80 shadow-xs">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold flex items-center gap-2">
          <UserRound className="h-4 w-4 text-primary" />
          Details of Officer Requesting
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 text-sm">
          <div>
            <span className="text-xs text-muted-foreground block font-medium">Requested By</span>
            <span className="font-semibold text-foreground">{fullName}</span>
          </div>
          <div>
            <span className="text-xs text-muted-foreground block font-medium">Employee ID</span>
            <span className="font-semibold text-foreground">{employee.employee_id || 'Not set'}</span>
          </div>
          <div>
            <span className="text-xs text-muted-foreground block font-medium">Department</span>
            <span className="font-semibold text-foreground">{employee.department_name || 'Not assigned'}</span>
          </div>
          <div>
            <span className="text-xs text-muted-foreground block font-medium">Designation</span>
            <span className="font-semibold text-foreground">{employee.position_title || 'Not assigned'}</span>
          </div>
          <div>
            <span className="text-xs text-muted-foreground block font-medium">Contact</span>
            <span className="font-semibold text-foreground">{employee.phone || employee.email || 'Not set'}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default RequesterInfoCard;


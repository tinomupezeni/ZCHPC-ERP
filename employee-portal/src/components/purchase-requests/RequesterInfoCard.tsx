import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { UserRound } from 'lucide-react';
import type { Employee } from '@/types/auth.types';

interface RequesterInfoCardProps {
  employee: Employee;
}

/**
 * Section A of the paper form (Details of Officer Requesting), read-only.
 * Every value here already comes from the authenticated employee's profile -
 * the same fields the backend itself uses to fill requester_name,
 * department_name, designation and contact when the request is created
 * (see modules.procurement.api.actors.requester_identity), so nothing here
 * is retyped by the employee.
 */
export function RequesterInfoCard({ employee }: RequesterInfoCardProps) {
  const fields: { label: string; value: string }[] = [
    { label: 'Requested By', value: employee.full_name },
    { label: 'Designation', value: employee.position_title || 'Not set' },
    { label: 'Contact', value: employee.phone || employee.email || 'Not set' },
    { label: 'Department', value: employee.department_name || 'Not set' },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <UserRound className="h-5 w-5" />
          Details of Officer Requesting
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          {fields.map((field) => (
            <div key={field.label}>
              <p className="text-muted-foreground">{field.label}</p>
              <p className="font-medium truncate">{field.value}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default RequesterInfoCard;

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { UserRound } from 'lucide-react';
import { DocumentFieldGrid, DocumentField } from '@/components/documents';
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
 *
 * Employee ID (F20) is available here (employee.employee_id, the EC number)
 * but deliberately isn't shown on the read-only PurchaseRequestDetail view of
 * an already-submitted request - the backend's PurchaseRequest response has
 * no EC-number field, only an internal numeric requester_id, and F20's own
 * "do not invent business fields" instruction rules out fabricating one
 * there. This form has the real authenticated employee object, so showing it
 * here is showing a field that actually exists, not inventing one.
 */
export function RequesterInfoCard({ employee }: RequesterInfoCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <UserRound className="h-5 w-5" />
          Details of Officer Requesting
        </CardTitle>
      </CardHeader>
      <CardContent>
        <DocumentFieldGrid>
          <DocumentField label="Requested By" value={employee.full_name} />
          <DocumentField label="Employee ID" value={employee.employee_id} />
          <DocumentField label="Designation" value={employee.position_title || 'Not set'} />
          <DocumentField
            label="Contact"
            value={employee.phone || employee.email || 'Not set'}
          />
          <DocumentField label="Department" value={employee.department_name || 'Not set'} />
        </DocumentFieldGrid>
      </CardContent>
    </Card>
  );
}

export default RequesterInfoCard;

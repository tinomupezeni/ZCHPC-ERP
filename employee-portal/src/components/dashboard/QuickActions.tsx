import { Link } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import {
  Clock,
  CalendarDays,
  FileText,
} from 'lucide-react';

interface QuickAction {
  icon: typeof Clock;
  label: string;
  description: string;
  color: string;
  href: string;
}

const quickActions: QuickAction[] = [
  {
    icon: Clock,
    label: 'Clock In/Out',
    description: 'Record attendance',
    color: 'bg-green-500',
    href: '/attendance',
  },
  {
    icon: CalendarDays,
    label: 'Request Leave',
    description: 'Submit application',
    color: 'bg-blue-500',
    href: '/leave',
  },
  {
    icon: FileText,
    label: 'View Payslips',
    description: 'Access payslips',
    color: 'bg-purple-500',
    href: '/payslips',
  },
];

export function QuickActions() {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Quick Actions</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {quickActions.map((action) => (
          <Link key={action.label} to={action.href}>
            <Card className="cursor-pointer hover:shadow-md transition-all hover:-translate-y-0.5 h-full">
              <CardContent className="p-4 flex flex-col items-center text-center">
                <div
                  className={`h-10 w-10 rounded-lg ${action.color} flex items-center justify-center mb-3`}
                >
                  <action.icon className="h-5 w-5 text-white" />
                </div>
                <h3 className="font-medium text-sm">{action.label}</h3>
                <p className="text-xs text-muted-foreground mt-1">
                  {action.description}
                </p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default QuickActions;

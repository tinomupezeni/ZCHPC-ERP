import { CalendarDays } from 'lucide-react';
import { format } from 'date-fns';

interface WelcomeCardProps {
  employeeName: string;
  employeeId: string;
  position: string | null;
  department: string | null;
}

export function WelcomeCard({
  employeeName,
  position,
  department,
}: WelcomeCardProps) {
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="bg-gradient-to-r from-primary/10 to-primary/5 rounded-xl p-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">
            {getGreeting()}, {employeeName.split(' ')[0]}!
          </h1>
          <p className="text-muted-foreground mt-1">
            {position && department
              ? `${position} - ${department}`
              : "Here's what's happening with your account today"}
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <CalendarDays className="h-4 w-4" />
          {format(new Date(), 'EEEE, MMMM d, yyyy')}
        </div>
      </div>
    </div>
  );
}

export default WelcomeCard;

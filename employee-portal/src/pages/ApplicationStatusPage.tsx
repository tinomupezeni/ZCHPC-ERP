import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Search,
  FileSearch,
  Briefcase,
  Calendar,
  CheckCircle,
  Clock,
  XCircle,
  Users,
  Award,
} from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';
import { jobsService } from '@/services/jobs.service';
import type { ApplicationStatus } from '@/types/jobs.types';

const statusConfig: Record<
  string,
  { color: string; icon: typeof Clock; label: string }
> = {
  Pending: { color: 'bg-yellow-500', icon: Clock, label: 'Pending Review' },
  Shortlisted: { color: 'bg-blue-500', icon: Users, label: 'Shortlisted' },
  Interview: { color: 'bg-purple-500', icon: Calendar, label: 'Interview Stage' },
  Offered: { color: 'bg-green-500', icon: Award, label: 'Offer Extended' },
  Hired: { color: 'bg-green-600', icon: CheckCircle, label: 'Hired' },
  Rejected: { color: 'bg-red-500', icon: XCircle, label: 'Not Selected' },
};

export function ApplicationStatusPage() {
  const [idNumber, setIdNumber] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [candidateName, setCandidateName] = useState<string | null>(null);
  const [applications, setApplications] = useState<ApplicationStatus[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!idNumber.trim()) {
      toast.error('Please enter your ID number');
      return;
    }

    try {
      setIsSearching(true);
      const result = await jobsService.getApplicationStatus(idNumber);
      setCandidateName(result.candidate_name);
      setApplications(result.applications);
      setHasSearched(true);
    } catch (err: any) {
      if (err.response?.status === 404) {
        setCandidateName(null);
        setApplications([]);
        setHasSearched(true);
      } else {
        toast.error('Failed to fetch application status');
      }
    } finally {
      setIsSearching(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const config = statusConfig[status] || statusConfig.Pending;
    const Icon = config.icon;

    return (
      <Badge
        className={`${config.color} text-white flex items-center gap-1`}
      >
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Application Status</h1>
        <p className="text-muted-foreground mt-1">
          Check the status of your job applications
        </p>
      </div>

      {/* Search Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Find Your Applications
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1">
              <Label htmlFor="id_number" className="sr-only">
                ID Number
              </Label>
              <Input
                id="id_number"
                value={idNumber}
                onChange={(e) => setIdNumber(e.target.value)}
                placeholder="Enter your National ID Number"
              />
            </div>
            <Button type="submit" disabled={isSearching}>
              {isSearching ? 'Searching...' : 'Check Status'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      {hasSearched && (
        <>
          {candidateName && applications.length > 0 ? (
            <div className="space-y-4">
              <Card>
                <CardContent className="p-4">
                  <p className="text-sm text-muted-foreground">
                    Showing applications for:
                  </p>
                  <p className="font-semibold text-lg">{candidateName}</p>
                </CardContent>
              </Card>

              <div className="space-y-4">
                {applications.map((app) => (
                  <Card key={app.id}>
                    <CardContent className="p-4">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                        <div className="flex items-start gap-3">
                          <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                            <Briefcase className="h-5 w-5 text-primary" />
                          </div>
                          <div>
                            <h3 className="font-semibold">{app.job_title}</h3>
                            {app.job_department && (
                              <p className="text-sm text-muted-foreground">
                                {app.job_department}
                              </p>
                            )}
                            <p className="text-sm text-muted-foreground flex items-center gap-1 mt-1">
                              <Calendar className="h-3 w-3" />
                              Applied on {format(new Date(app.applied_on), 'MMMM d, yyyy')}
                            </p>
                          </div>
                        </div>
                        <div>{getStatusBadge(app.status)}</div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <FileSearch className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="font-semibold text-lg">No Applications Found</h3>
                <p className="text-muted-foreground mt-1">
                  We couldn't find any job applications with the ID number you provided.
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  Please check that you entered the correct ID number, or browse
                  our current job openings to apply.
                </p>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Info */}
      {!hasSearched && (
        <Card>
          <CardContent className="p-6">
            <h3 className="font-semibold mb-3">Application Status Guide</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              {Object.entries(statusConfig).map(([key, config]) => {
                const Icon = config.icon;
                return (
                  <div key={key} className="flex items-center gap-2">
                    <div
                      className={`h-6 w-6 rounded ${config.color} flex items-center justify-center`}
                    >
                      <Icon className="h-3 w-3 text-white" />
                    </div>
                    <span className="text-sm">{config.label}</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default ApplicationStatusPage;

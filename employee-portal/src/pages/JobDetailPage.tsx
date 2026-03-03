import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  MapPin,
  Calendar,
  Briefcase,
  DollarSign,
  Building,
  Clock,
  ArrowLeft,
  Users,
} from 'lucide-react';
import { format } from 'date-fns';
import { jobsService } from '@/services/jobs.service';
import type { Job } from '@/types/jobs.types';

export function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadJob(parseInt(id));
    }
  }, [id]);

  const loadJob = async (jobId: number) => {
    try {
      setIsLoading(true);
      const data = await jobsService.getJob(jobId);
      setJob(data);
    } catch (err) {
      setError('Job not found or no longer accepting applications.');
      console.error('Failed to load job:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatSalary = (min: number | null, max: number | null) => {
    if (!min && !max) return 'Competitive';
    if (min && max) return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
    if (min) return `From $${min.toLocaleString()}`;
    return `Up to $${max?.toLocaleString()}`;
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Jobs
        </Button>
        <Card className="animate-pulse">
          <CardContent className="p-6">
            <div className="h-8 bg-muted rounded w-1/2 mb-4"></div>
            <div className="h-4 bg-muted rounded w-1/3 mb-6"></div>
            <div className="space-y-2">
              <div className="h-4 bg-muted rounded w-full"></div>
              <div className="h-4 bg-muted rounded w-full"></div>
              <div className="h-4 bg-muted rounded w-3/4"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => navigate('/careers')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Jobs
        </Button>
        <Card>
          <CardContent className="p-8 text-center">
            <Briefcase className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="font-semibold text-lg">Job Not Found</h3>
            <p className="text-muted-foreground mt-1">{error}</p>
            <Link to="/careers">
              <Button className="mt-4">View All Jobs</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Button variant="ghost" onClick={() => navigate('/careers')}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Jobs
      </Button>

      {/* Job Header */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Briefcase className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">{job.title}</h1>
                  {job.department && (
                    <p className="text-muted-foreground">{job.department}</p>
                  )}
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3 mt-4 text-sm">
                {job.location && (
                  <Badge variant="secondary" className="flex items-center gap-1">
                    <MapPin className="h-3 w-3" />
                    {job.location}
                  </Badge>
                )}
                <Badge variant="secondary" className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {job.employment_type}
                </Badge>
                <Badge variant="secondary" className="flex items-center gap-1">
                  <DollarSign className="h-3 w-3" />
                  {formatSalary(job.salary_min, job.salary_max)}
                </Badge>
                {job.application_count !== undefined && (
                  <Badge variant="outline" className="flex items-center gap-1">
                    <Users className="h-3 w-3" />
                    {job.application_count} applicant{job.application_count !== 1 ? 's' : ''}
                  </Badge>
                )}
              </div>

              {job.closing_date && (
                <p className="text-sm text-muted-foreground mt-3 flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  Application deadline: {format(new Date(job.closing_date), 'MMMM d, yyyy')}
                </p>
              )}
            </div>

            <Link to={`/careers/${job.id}/apply`}>
              <Button size="lg" className="w-full md:w-auto">
                Apply for this Position
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Job Details */}
      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-2 space-y-6">
          {/* Description */}
          <Card>
            <CardHeader>
              <CardTitle>Job Description</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none">
                <p className="whitespace-pre-wrap">{job.description}</p>
              </div>
            </CardContent>
          </Card>

          {/* Requirements */}
          {job.requirements && (
            <Card>
              <CardHeader>
                <CardTitle>Requirements</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none">
                  <p className="whitespace-pre-wrap">{job.requirements}</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Responsibilities */}
          {job.responsibilities && (
            <Card>
              <CardHeader>
                <CardTitle>Responsibilities</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none">
                  <p className="whitespace-pre-wrap">{job.responsibilities}</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Job Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <Building className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Department</p>
                  <p className="text-sm text-muted-foreground">
                    {job.department || 'Not specified'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <MapPin className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Location</p>
                  <p className="text-sm text-muted-foreground">
                    {job.location || 'Not specified'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Clock className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Employment Type</p>
                  <p className="text-sm text-muted-foreground">
                    {job.employment_type}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <DollarSign className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Salary Range</p>
                  <p className="text-sm text-muted-foreground">
                    {formatSalary(job.salary_min, job.salary_max)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Calendar className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Posted On</p>
                  <p className="text-sm text-muted-foreground">
                    {format(new Date(job.posted_date), 'MMMM d, yyyy')}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <Link to={`/careers/${job.id}/apply`}>
                <Button className="w-full" size="lg">
                  Apply Now
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default JobDetailPage;

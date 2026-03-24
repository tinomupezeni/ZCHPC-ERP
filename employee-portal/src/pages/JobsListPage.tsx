import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  MapPin,
  Calendar,
  Briefcase,
  DollarSign,
  Building,
  Clock,
  Users,
  ArrowRight,
  Search,
  Loader2,
} from 'lucide-react';
import { format } from 'date-fns';
import { jobsService } from '@/services/jobs.service';
import type { Job } from '@/types/jobs.types';

export function JobsListPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    try {
      setIsLoading(true);
      const response = await jobsService.getJobs();
      // Handle both array response and { jobs: [] } response
      const jobsList = Array.isArray(response) ? response : (response.jobs || []);
      setJobs(jobsList);
    } catch (err) {
      setError('Failed to load job listings. Please try again later.');
      console.error('Failed to load jobs:', err);
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
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="h-10 w-10 text-blue-600 animate-spin mx-auto mb-4" />
            <p className="text-slate-600">Loading job listings...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-8 text-center">
            <div className="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
              <Search className="h-6 w-6 text-red-600" />
            </div>
            <h3 className="font-semibold text-lg text-red-800">Unable to Load Jobs</h3>
            <p className="text-red-600 mt-1">{error}</p>
            <Button onClick={loadJobs} className="mt-4 bg-red-600 hover:bg-red-700">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Bar */}
      <div className="flex flex-wrap gap-4 items-center justify-between">
        <div>
          <p className="text-slate-600">
            <span className="text-2xl font-bold text-slate-900">{jobs.length}</span>
            {' '}open position{jobs.length !== 1 ? 's' : ''} available
          </p>
        </div>
        <Link to="/careers/status">
          <Button variant="outline" className="gap-2 border-blue-200 text-blue-700 hover:bg-blue-50">
            <Search className="h-4 w-4" />
            Check Application Status
          </Button>
        </Link>
      </div>

      {jobs.length === 0 ? (
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-12 text-center">
            <div className="h-16 w-16 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-4">
              <Briefcase className="h-8 w-8 text-blue-600" />
            </div>
            <h3 className="font-semibold text-xl text-slate-900">No Open Positions</h3>
            <p className="text-slate-600 mt-2 max-w-md mx-auto">
              There are currently no job openings available. Please check back later
              or sign up for job alerts to be notified when new positions are posted.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {jobs.map((job) => (
            <Card
              key={job.id}
              className="border-slate-200 shadow-sm hover:shadow-lg hover:border-blue-200 transition-all duration-200 group"
            >
              <CardContent className="p-6">
                <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-start gap-4">
                      <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-blue-500/25">
                        <Briefcase className="h-6 w-6 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h2 className="text-xl font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                          {job.title}
                        </h2>
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-2">
                          {job.department && (
                            <span className="flex items-center gap-1.5 text-sm text-slate-600">
                              <Building className="h-4 w-4 text-slate-400" />
                              {job.department}
                            </span>
                          )}
                          {job.location && (
                            <span className="flex items-center gap-1.5 text-sm text-slate-600">
                              <MapPin className="h-4 w-4 text-slate-400" />
                              {job.location}
                            </span>
                          )}
                          <span className="flex items-center gap-1.5 text-sm text-slate-600">
                            <Clock className="h-4 w-4 text-slate-400" />
                            {job.employment_type}
                          </span>
                        </div>
                      </div>
                    </div>

                    {job.description && (
                      <p className="text-sm text-slate-600 mt-4 line-clamp-2 leading-relaxed">
                        {job.description}
                      </p>
                    )}

                    <div className="flex flex-wrap items-center gap-2 mt-4">
                      <Badge className="bg-green-100 text-green-700 hover:bg-green-100 font-medium">
                        <DollarSign className="h-3.5 w-3.5 mr-1" />
                        {formatSalary(job.salary_min, job.salary_max)}
                      </Badge>
                      {job.closing_date && (
                        <Badge variant="outline" className="text-slate-600 border-slate-300">
                          <Calendar className="h-3.5 w-3.5 mr-1" />
                          Closes: {format(new Date(job.closing_date), 'MMM d, yyyy')}
                        </Badge>
                      )}
                      {job.posted_date && (
                        <Badge variant="outline" className="text-slate-500 border-slate-200">
                          Posted: {format(new Date(job.posted_date), 'MMM d, yyyy')}
                        </Badge>
                      )}
                      {job.is_internal && (
                        <Badge className="bg-purple-100 text-purple-700 hover:bg-purple-100">
                          <Users className="h-3.5 w-3.5 mr-1" />
                          Internal Only
                        </Badge>
                      )}
                    </div>
                  </div>

                  <div className="flex lg:flex-col gap-2 lg:w-auto">
                    <Link to={`/careers/${job.id}`} className="flex-1 lg:flex-none">
                      <Button className="w-full bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-600/25 gap-2">
                        View Details
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                    </Link>
                    <Link to={`/careers/${job.id}/apply`} className="flex-1 lg:flex-none">
                      <Button
                        variant="outline"
                        className="w-full border-blue-200 text-blue-700 hover:bg-blue-50 hover:border-blue-300"
                      >
                        Quick Apply
                      </Button>
                    </Link>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Info Cards */}
      <div className="grid md:grid-cols-2 gap-4 mt-8">
        <Card className="border-slate-200 bg-gradient-to-br from-blue-50 to-white">
          <CardContent className="p-6">
            <h3 className="font-semibold text-slate-900 mb-2">How to Apply</h3>
            <ol className="text-sm text-slate-600 space-y-2">
              <li className="flex items-start gap-2">
                <span className="h-5 w-5 rounded-full bg-blue-600 text-white text-xs flex items-center justify-center flex-shrink-0 mt-0.5">1</span>
                <span>Browse available positions and find one that matches your skills</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="h-5 w-5 rounded-full bg-blue-600 text-white text-xs flex items-center justify-center flex-shrink-0 mt-0.5">2</span>
                <span>Click &quot;View Details&quot; to read the full job description</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="h-5 w-5 rounded-full bg-blue-600 text-white text-xs flex items-center justify-center flex-shrink-0 mt-0.5">3</span>
                <span>Submit your application with your resume and cover letter</span>
              </li>
            </ol>
          </CardContent>
        </Card>
        <Card className="border-slate-200 bg-gradient-to-br from-slate-50 to-white">
          <CardContent className="p-6">
            <h3 className="font-semibold text-slate-900 mb-2">Already Applied?</h3>
            <p className="text-sm text-slate-600 mb-4">
              Track the status of your application using your National ID number.
              You&apos;ll be able to see if your application is pending, under review,
              or if you&apos;ve been shortlisted for an interview.
            </p>
            <Link to="/careers/status">
              <Button variant="outline" size="sm" className="gap-2">
                <Search className="h-4 w-4" />
                Check Status
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default JobsListPage;

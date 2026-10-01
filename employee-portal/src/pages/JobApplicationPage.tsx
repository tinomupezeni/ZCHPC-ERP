import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  ArrowLeft,
  Briefcase,
  Upload,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { toast } from 'sonner';
import { jobsService } from '@/services/jobs.service';
import type { Job, JobApplicationFormData } from '@/types/jobs.types';

export function JobApplicationPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCheckingId, setIsCheckingId] = useState(false);
  const [hasAlreadyApplied, setHasAlreadyApplied] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const [formData, setFormData] = useState<JobApplicationFormData>({
    job_id: 0,
    id_number: '',
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    address: '',
    date_of_birth: '',
    qualifications: '',
    experience: '',
    cover_letter: '',
  });

  const [resume, setResume] = useState<File | null>(null);

  useEffect(() => {
    if (id) {
      loadJob(parseInt(id));
      setFormData((prev) => ({ ...prev, job_id: parseInt(id) }));
    }
  }, [id]);

  const loadJob = async (jobId: number) => {
    try {
      setIsLoading(true);
      const data = await jobsService.getJob(jobId);
      setJob(data);
    } catch (err) {
      toast.error('Job not found or no longer accepting applications.');
      navigate('/careers');
    } finally {
      setIsLoading(false);
    }
  };

  const checkExistingApplication = async () => {
    if (!formData.id_number || formData.id_number.length < 5) return;

    try {
      setIsCheckingId(true);
      const result = await jobsService.checkApplication(
        formData.id_number,
        formData.job_id
      );

      if (result.has_applied) {
        setHasAlreadyApplied(true);
        toast.error('You have already applied for this position.');
      } else {
        setHasAlreadyApplied(false);
      }
    } catch (err) {
      console.error('Error checking application:', err);
    } finally {
      setIsCheckingId(false);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file size (5MB max)
      if (file.size > 5 * 1024 * 1024) {
        toast.error('File size must be less than 5MB');
        return;
      }
      // Validate file type
      const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      ];
      if (!allowedTypes.includes(file.type)) {
        toast.error('Please upload a PDF or Word document');
        return;
      }
      setResume(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (hasAlreadyApplied) {
      toast.error('You have already applied for this position.');
      return;
    }

    // Validate required fields
    if (
      !formData.id_number ||
      !formData.first_name ||
      !formData.last_name ||
      !formData.email
    ) {
      toast.error('Please fill in all required fields.');
      return;
    }

    try {
      setIsSubmitting(true);
      await jobsService.submitApplication({
        ...formData,
        resume: resume || undefined,
      });

      setSubmitted(true);
      toast.success('Application submitted successfully!');
    } catch (err: any) {
      const message =
        err.response?.data?.detail || 'Failed to submit application.';
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Card className="animate-pulse">
          <CardContent className="p-6">
            <div className="h-8 bg-muted rounded w-1/2 mb-4"></div>
            <div className="h-4 bg-muted rounded w-1/3"></div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="p-8 text-center">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Application Submitted!</h2>
            <p className="text-muted-foreground mb-6">
              Thank you for applying for the position of{' '}
              <strong>{job?.title}</strong>. We have received your application
              and will review it shortly.
            </p>
            <p className="text-sm text-muted-foreground mb-6">
              You can check the status of your application using your ID number
              on the Application Status page.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link to="/careers">
                <Button variant="outline">View More Jobs</Button>
              </Link>
              <Link to="/careers/status">
                <Button>Check Application Status</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Button variant="ghost" onClick={() => navigate(-1)}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back
      </Button>

      {/* Job Info */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Briefcase className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold">Apply for: {job?.title}</h2>
              {job?.department && (
                <p className="text-sm text-muted-foreground">{job.department}</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Application Form */}
      <form onSubmit={handleSubmit}>
        <div className="grid gap-6">
          {/* Personal Information */}
          <Card>
            <CardHeader>
              <CardTitle>Personal Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="id_number">
                    National ID Number <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="id_number"
                    name="id_number"
                    value={formData.id_number}
                    onChange={handleInputChange}
                    onBlur={checkExistingApplication}
                    placeholder="Enter your ID number"
                    required
                  />
                  {isCheckingId && (
                    <p className="text-sm text-muted-foreground">
                      Checking application status...
                    </p>
                  )}
                  {hasAlreadyApplied && (
                    <p className="text-sm text-destructive flex items-center gap-1">
                      <AlertCircle className="h-4 w-4" />
                      You have already applied for this position
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="date_of_birth">Date of Birth</Label>
                  <Input
                    id="date_of_birth"
                    name="date_of_birth"
                    type="date"
                    value={formData.date_of_birth}
                    onChange={handleInputChange}
                  />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="first_name">
                    First Name <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="first_name"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleInputChange}
                    placeholder="Enter your first name"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="last_name">
                    Last Name <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="last_name"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleInputChange}
                    placeholder="Enter your last name"
                    required
                  />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="email">
                    Email Address <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    placeholder="Enter your email"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input
                    id="phone"
                    name="phone"
                    type="tel"
                    value={formData.phone}
                    onChange={handleInputChange}
                    placeholder="Enter your phone number"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="address">Address</Label>
                <Textarea
                  id="address"
                  name="address"
                  value={formData.address}
                  onChange={handleInputChange}
                  placeholder="Enter your full address"
                  rows={2}
                />
              </div>
            </CardContent>
          </Card>

          {/* Professional Information */}
          <Card>
            <CardHeader>
              <CardTitle>Professional Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="qualifications">Educational Qualifications</Label>
                <Textarea
                  id="qualifications"
                  name="qualifications"
                  value={formData.qualifications}
                  onChange={handleInputChange}
                  placeholder="List your educational qualifications, degrees, certifications..."
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="experience">Work Experience</Label>
                <Textarea
                  id="experience"
                  name="experience"
                  value={formData.experience}
                  onChange={handleInputChange}
                  placeholder="Describe your relevant work experience..."
                  rows={4}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="cover_letter">Cover Letter / Motivation</Label>
                <Textarea
                  id="cover_letter"
                  name="cover_letter"
                  value={formData.cover_letter}
                  onChange={handleInputChange}
                  placeholder="Tell us why you're interested in this position and why you would be a great fit..."
                  rows={5}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="resume">
                  Resume / CV
                  <Badge variant="secondary" className="ml-2">
                    PDF or Word
                  </Badge>
                </Label>
                <div className="border-2 border-dashed rounded-lg p-4">
                  <input
                    id="resume"
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <label
                    htmlFor="resume"
                    className="flex flex-col items-center gap-2 cursor-pointer"
                  >
                    <Upload className="h-8 w-8 text-muted-foreground" />
                    {resume ? (
                      <div className="text-center">
                        <p className="font-medium">{resume.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {(resume.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    ) : (
                      <div className="text-center">
                        <p className="font-medium">Click to upload your resume</p>
                        <p className="text-sm text-muted-foreground">
                          PDF or Word document, max 5MB
                        </p>
                      </div>
                    )}
                  </label>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Submit */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col sm:flex-row gap-3 justify-end">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate(-1)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSubmitting || hasAlreadyApplied}
                >
                  {isSubmitting ? 'Submitting...' : 'Submit Application'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </form>
    </div>
  );
}

export default JobApplicationPage;

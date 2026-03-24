# Recruitment Module

Job postings and hiring pipeline.

## Domain

### Aggregates

**Job** (root):
- id, title
- department_id, position_id
- status (Draft, Open, Closed)
- location, reports_to
- salary_usd_min/max, salary_zig_min/max
- description, responsibilities, qualifications, competencies
- application_process, contact_email
- is_internal, posted_date

**Candidate** (root):
- id, national_id
- first_name, last_name
- email, phone, address
- date_of_birth
- qualifications, experience
- resume_path

**Application** (root):
- id, job_id, candidate_id
- cover_letter
- status (Pending, Shortlisted, Interview, Offered, Hired, Rejected)
- applied_at, updated_at

### Value Objects

- `JobStatus`: Draft, Open, Closed
- `ApplicationStatus`: Pending, Shortlisted, Interview, Offered, Hired, Rejected
- `SalaryRange`: min, max, currency

### Domain Services

- `ApplicationProcessor`: Status transitions
- `HiringService`: Convert candidate to employee

### Events

- `JobPosted`
- `JobClosed`
- `ApplicationReceived`
- `ApplicationStatusChanged`
- `CandidateHired`

## API Endpoints

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/recruitment/jobs/` | List jobs |
| POST | `/api/recruitment/jobs/` | Create job |
| PUT | `/api/recruitment/jobs/{id}/` | Update job |
| GET | `/api/recruitment/applications/` | List applications |
| PUT | `/api/recruitment/applications/{id}/` | Update status |

### Public

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/careers/` | Public job listings |
| GET | `/api/careers/{id}/` | Job details |
| POST | `/api/careers/{id}/apply/` | Submit application |

## Dependencies

- HR Module (IEmployeeProvider for creating employee on hire)

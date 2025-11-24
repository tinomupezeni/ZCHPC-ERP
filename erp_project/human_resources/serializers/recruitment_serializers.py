from rest_framework import serializers
from ..hr_models import Job, Department, JobApplication, Candidate

class JobSerializer(serializers.ModelSerializer):
    # 1. Read as String (e.g. "IT Department")
    department = serializers.StringRelatedField(read_only=True)
    
    # 2. Write as ID (e.g. 1)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True,
        required=False,
        allow_null=True
    )

    # 3. Map Frontend fields to Backend fields
    # The source='field_name' tells DRF where to find the data in the model
    postedDate = serializers.DateField(source='posted_date')
    salaryRange = serializers.CharField(source='salary_range', required=False, allow_blank=True)
    contactEmail = serializers.EmailField(source='contact_email')
    applicationProcess = serializers.CharField(source='application_process', required=False, allow_blank=True)
    
    # JSONFields are handled automatically as Lists by DRF
    
    applicants = serializers.IntegerField(source='applicants_count', read_only=True)

    class Meta:
        model = Job
        fields = [
            'id', 
            'title', 
            'department', 'department_id', # Read & Write
            'status', 
            'location',
            'description',
            'responsibilities', # JSON List
            'qualifications',   # JSON List
            'notes',
            # Mapped Fields
            'postedDate', 
            'salaryRange',
            'contactEmail',
            'applicationProcess',
            'applicants'
        ]

class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = '__all__'

class JobApplicationSerializer(serializers.ModelSerializer):
    candidate = CandidateSerializer(read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)

    class Meta:
        model = JobApplication
        fields = ['id', 'job', 'job_title', 'candidate', 'applied_on', 'status']
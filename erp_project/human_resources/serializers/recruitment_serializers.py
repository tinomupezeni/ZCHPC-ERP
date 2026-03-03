from datetime import timezone
from rest_framework import serializers
from ..hr_models import Job, Department, JobApplication, Candidate, Position

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
    
    # 3. Position handling
    position_id = serializers.PrimaryKeyRelatedField(
        queryset=Position.objects.all(),
        source='position',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    # 4. Map Frontend camelCase fields to Backend snake_case fields
    postedDate = serializers.DateField(source='posted_date', required=False)
    salaryRange = serializers.CharField(source='salary_range', required=False, allow_blank=True)
    contactEmail = serializers.EmailField(source='contact_email', required=False)
    applicationProcess = serializers.CharField(source='application_process', required=False, allow_blank=True)
    reportsTo = serializers.CharField(source='reports_to', required=False, allow_blank=True)
    isInternal = serializers.BooleanField(source='is_internal', required=False)

    # Multi-currency salary fields (camelCase for frontend)
    salaryUsdMin = serializers.DecimalField(source='salary_usd_min', max_digits=12, decimal_places=2, required=False, allow_null=True)
    salaryUsdMax = serializers.DecimalField(source='salary_usd_max', max_digits=12, decimal_places=2, required=False, allow_null=True)
    salaryZigMin = serializers.DecimalField(source='salary_zig_min', max_digits=12, decimal_places=2, required=False, allow_null=True)
    salaryZigMax = serializers.DecimalField(source='salary_zig_max', max_digits=12, decimal_places=2, required=False, allow_null=True)
    
    # JSONFields are handled automatically as Lists by DRF
    # But we'll be explicit for clarity
    responsibilities = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
        required=False,
        allow_empty=True
    )
    qualifications = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
        required=False,
        allow_empty=True
    )
    competencies = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
        required=False,
        allow_empty=True
    )
    
    applicants = serializers.IntegerField(source='applicants_count', read_only=True)

    class Meta:
        model = Job
        fields = [
            'id',
            'title',
            'department',
            'department_id',
            'position_id',
            'status',
            'location',
            'description',
            'responsibilities',
            'qualifications',
            'competencies',
            'notes',
            # Mapped Fields (camelCase for frontend)
            'postedDate',
            'salaryRange',
            'salaryUsdMin',
            'salaryUsdMax',
            'salaryZigMin',
            'salaryZigMax',
            'contactEmail',
            'applicationProcess',
            'reportsTo',
            'isInternal',
            'applicants'
        ]
    
    def validate(self, data):
        """
        Custom validation to ensure data integrity
        """
        # Filter out empty strings from list fields
        for field in ['responsibilities', 'qualifications', 'competencies']:
            if field in data:
                data[field] = [item.strip() for item in data[field] if item and item.strip()]
        
        return data
    
    def create(self, validated_data):
        """
        Handle creation with proper defaults
        """
        # Set defaults if not provided
        if 'posted_date' not in validated_data:
            validated_data['posted_date'] = timezone.localdate()
        
        if 'contact_email' not in validated_data:
            validated_data['contact_email'] = 'hroffice@zchpc.ac.zw'
        
        if 'reports_to' not in validated_data:
            validated_data['reports_to'] = 'ZCHPC Director'
        
        if 'is_internal' not in validated_data:
            validated_data['is_internal'] = False
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """
        Handle updates properly
        """
        # Update all fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


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
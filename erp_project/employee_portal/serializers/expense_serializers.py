from rest_framework import serializers
from django.utils import timezone
from ..models import ExpenseCategory, ExpenseClaim


class ExpenseCategorySerializer(serializers.ModelSerializer):
    """Serializer for expense categories"""
    class Meta:
        model = ExpenseCategory
        fields = ['id', 'name', 'description', 'max_amount', 'requires_receipt']


class ExpenseClaimListSerializer(serializers.ModelSerializer):
    """Serializer for listing expense claims"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    can_edit = serializers.BooleanField(read_only=True)
    can_submit = serializers.BooleanField(read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    has_receipt = serializers.SerializerMethodField()

    class Meta:
        model = ExpenseClaim
        fields = [
            'id', 'title', 'category', 'category_name', 'amount', 'currency',
            'date_incurred', 'status', 'has_receipt', 'submitted_at',
            'created_at', 'can_edit', 'can_submit', 'can_cancel'
        ]

    def get_has_receipt(self, obj):
        return bool(obj.receipt)


class ExpenseClaimDetailSerializer(serializers.ModelSerializer):
    """Serializer for expense claim details"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()
    can_edit = serializers.BooleanField(read_only=True)
    can_submit = serializers.BooleanField(read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    receipt_url = serializers.SerializerMethodField()

    class Meta:
        model = ExpenseClaim
        fields = [
            'id', 'title', 'description', 'category', 'category_name',
            'amount', 'currency', 'date_incurred', 'receipt', 'receipt_url',
            'status', 'submitted_at', 'reviewed_by_name', 'reviewed_at',
            'review_notes', 'paid_at', 'payment_reference',
            'created_at', 'updated_at', 'can_edit', 'can_submit', 'can_cancel'
        ]

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return f"{obj.reviewed_by.first_name} {obj.reviewed_by.surname}"
        return None

    def get_receipt_url(self, obj):
        if obj.receipt:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.receipt.url)
            return obj.receipt.url
        return None


class CreateExpenseClaimSerializer(serializers.ModelSerializer):
    """Serializer for creating expense claims"""
    class Meta:
        model = ExpenseClaim
        fields = [
            'title', 'description', 'category', 'amount', 'currency',
            'date_incurred', 'receipt'
        ]

    def validate_date_incurred(self, value):
        """Ensure date is not in the future"""
        if value > timezone.now().date():
            raise serializers.ValidationError("Date incurred cannot be in the future.")
        return value

    def validate(self, data):
        """Validate the expense claim"""
        category = data.get('category')
        amount = data.get('amount')

        # Check max amount for category
        if category and category.max_amount and amount:
            if amount > category.max_amount:
                raise serializers.ValidationError({
                    'amount': f'Amount exceeds maximum allowed ({category.max_amount}) for this category.'
                })

        return data

    def create(self, validated_data):
        """Create expense claim for current employee"""
        validated_data['employee'] = self.context['request'].user.employee_profile
        return super().create(validated_data)


class UpdateExpenseClaimSerializer(serializers.ModelSerializer):
    """Serializer for updating draft expense claims"""
    class Meta:
        model = ExpenseClaim
        fields = [
            'title', 'description', 'category', 'amount', 'currency',
            'date_incurred', 'receipt'
        ]

    def validate_date_incurred(self, value):
        """Ensure date is not in the future"""
        if value > timezone.now().date():
            raise serializers.ValidationError("Date incurred cannot be in the future.")
        return value

    def validate(self, data):
        """Validate the expense claim"""
        instance = self.instance

        # Can only update draft claims
        if instance and instance.status != 'Draft':
            raise serializers.ValidationError("Only draft claims can be updated.")

        category = data.get('category', instance.category if instance else None)
        amount = data.get('amount', instance.amount if instance else None)

        # Check max amount for category
        if category and category.max_amount and amount:
            if amount > category.max_amount:
                raise serializers.ValidationError({
                    'amount': f'Amount exceeds maximum allowed ({category.max_amount}) for this category.'
                })

        return data


class ExpenseClaimSummarySerializer(serializers.Serializer):
    """Serializer for expense claim summary"""
    total_claims = serializers.IntegerField()
    draft_claims = serializers.IntegerField()
    pending_claims = serializers.IntegerField()
    approved_claims = serializers.IntegerField()
    rejected_claims = serializers.IntegerField()
    paid_claims = serializers.IntegerField()
    total_amount_pending = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_amount_approved = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2)

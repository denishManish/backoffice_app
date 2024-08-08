from django.contrib.auth.models import Group
from rest_framework import serializers
from drf_writable_nested.serializers import WritableNestedModelSerializer
from drf_writable_nested.mixins import UniqueFieldsMixin
from .models import Partner, Employee, Branch
from user_management.serializers import UserSerializer


class PartnerSerializer(serializers.ModelSerializer):
    """
    Serializer for the Partner model.
    Validates that the owner of the partner is in the 'owner' group. 
    Excludes 'courses' from serialization.

    Attributes: Meta
        model (`django.db.models.Model`): `Partner` model to serialize.
        exclude (List): `['courses']` <br>
            all fields of the model to serialize except `courses`.

    Methods:
        validate: 
            Ensures that owner of the partner have 'owner' group.
        to_representation: 
            Translates the 'status' field.
    """
    class Meta:
        model = Partner
        exclude = ['courses']

    def validate(self, data):
        """
        Validate that the owner of the partner is part of the 'owner' group.

        Args:
            data (dict): Serialized data to validate.

        Returns:
            (dict): The validated data.

        Raises:
            ValidationError: If the owner is not in the 'owner' group.
        """
        if 'owner' in data and not data['owner'].groups.filter(name='owner').exists():
            raise serializers.ValidationError("Owner must be in an owner group.")
        return super().validate(data)
    
    def to_representation(self, instance):
        """
        Convert a Partner instance into a dictionary format that can be serialized. <br>
        Translate the 'status' field by the language of the request. Default is 'en'. 

        Args:
            instance (Partner): The Partner instance to be serialized.

        Returns:
            (dict): A dictionary representing the serialized Partner instance.
        """
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation

  
class PartnerDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Partner model, providing counts of related branches and employees.
    Excludes 'courses' from serialization.

    Attributes:
        quantity_of_branches (SerializerMethodField): 
            Number of partner's branches.
        quantity_of_employees (SerializerMethodField): 
            Number of partner's employees.

    Methods:
        get_quantity_of_branches:
            Counts the branches associated with the partner.
        get_quantity_of_employees:
            Counts the employees associated with the partner.
        to_representation: 
            Translates the 'status' field.
    """
    quantity_of_branches = serializers.SerializerMethodField()
    quantity_of_employees = serializers.SerializerMethodField()

    class Meta:
        model = Partner 
        exclude = ['courses']

    def get_quantity_of_branches(self, obj):
        """
        Return the count of branches associated with the partner.

        Args:
            obj (Partner): The `Partner` instance.

        Returns:
            (int): Number of branches.
        """
        return obj.branches.count()

    def get_quantity_of_employees(self, obj):
        """
        Return the count of employees associated with the partner.

        Args:
            obj (Partner): The `Partner` instance.

        Returns:
            (int): Number of employees.
        """
        return obj.employees.count()

    def to_representation(self, instance):
        """
        Convert a Partner instance into a dictionary format that can be serialized. <br>
        Translate the 'status' field by the language of the request. Default is 'en'. 

        Args:
            instance (Partner): The Partner instance to be serialized.

        Returns:
            (dict): A dictionary representing the serialized Partner instance.
        """
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation


class EmployeeSerializer(UniqueFieldsMixin, WritableNestedModelSerializer):
    """
    Serializer for Employee model with nested User data.
    This serializer allows writable nested serialization(`WritableNestedModelSerializer`) 
        and handles unique field constraints(`UniqueFieldsMixin`).

    Attributes:
        user (UserSerializer): Nested serializer for user data.

    Attributes: Meta
        model (`django.db.models.Model`): `Employee` model to serialize.
        fields (List): `__all__` <br>
            all fields of the model to serialize.
        extra_kwargs (dict): Additional keyword arguments for fields configuration. <br>
            Makes `branches`, `courses` fields optional.

    Methods:
        to_representation: 
            Translates the 'status' field.
    """
    user = UserSerializer()

    class Meta:
        model = Employee
        fields = '__all__'
        extra_kwargs = {
            'branches': {'required': False, 'allow_empty': True},
            'courses': {'required': False, 'allow_empty': True}
        }
    
    def to_representation(self, instance):
        """
        Convert a Employee instance into a dictionary format that can be serialized. <br>
        Translate the 'status' field by the language of the request. Default is 'en'. 

        Args:
            instance (Employee): The Employee instance to be serialized.

        Returns:
            (dict): A dictionary representing the serialized Employee instance.
        """
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation


class EmployeeSerializerForOwner(EmployeeSerializer):
    """
    Specialized Employee serializer for owners, disallowing employees to be assigned `superuser`status and 
        automatically assigns the authenticated user's owned partner to the employee.

    Methods:
        validate_user: Ensures that owner can't grant to employee superuser group.
        create: Custom creation logic to assign the partner field based on the request's user.
    """
    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ['partner']
        extra_kwargs = {
            'branches': {'required': False, 'allow_empty': True},
            'courses': {'required': False, 'allow_empty': True}
        }

    def validate_user(self, value):
        """
        Validate that the employee is not a superuser.

        Args:
            value (dict): The user data being validated.

        Returns:
            (dict): Validated user data.

        Raises:
            ValidationError: If the user's group is a superuser.
        """
        if value.get('group') and Group.objects.get(name='superuser') == value['group']:
            raise serializers.ValidationError("Employee can't be a superuser.")
        return value
    
    def create(self, validated_data):
        """
        Custom creation logic to assign the partner field based on the request's user.

        Args:
            validated_data (dict): The raw validated data.

        Returns:
            (Employee): The newly created Employee instance.
        """
        request = self.context['request']
        validated_data['partner'] = request.user.owned_partner
        return super().create(validated_data)
    

class BranchSerializer(serializers.ModelSerializer):
    """
    Serializer for Branch model.

    Attributes:
        employees (PrimaryKeyRelatedField): __ManyToManyField from `Employee` model__ <br>
            List of employees assigned to the branch. <br>
            Accessible as `employees`, accessible in query as `employee`.

    Attributes: Meta
        model (`django.db.models.Model`): `Branch` model to serialize.
        fields (List): `__all__` <br>
            all fields of the model to serialize.

    Methods:
        validate: 
            Ensure that assigned employees are valid under the current branch's partner.
        to_representation: 
            Translates the 'status' field.
    """
    employees = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Employee.objects.all(), 
        allow_null=True, 
        required=False
    )
    class Meta:
        model = Branch
        fields = '__all__'

    def validate(self, data):
        """
        Ensure that assigned employees are valid under the current branch's partner.
        If an employee is connected to another partner than the branch, it is removed from the list.

        Args:
            data (dict): Serialized data to validate.

        Returns:
            (dict): The validated data.
        """
        partner = data.get('partner', self.instance.partner if self.instance else None)
        employees_data = data.get('employees', self.instance.employees.all() if self.instance else Employee.objects.none())

        if 'employees' not in data:
            return data
        
        valid_employees = [employee for employee in employees_data if employee.partner == partner]
        data['employees'] = valid_employees
        return data

    def to_representation(self, instance):
        """
        Convert a Branch instance into a dictionary format that can be serialized. <br>
        Translate the 'status' field by the language of the request. Default is 'en'. 

        Args:
            instance (Branch): The Branch instance to be serialized.

        Returns:
            (dict): A dictionary representing the serialized Branch instance.
        """
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation


    #that's filtering employees field and return representation with ids amd emails
    #def __init__(self, *args, **kwargs):
    #    super().__init__(*args, **kwargs)
    #    if 'context' in kwargs and kwargs['context'].get('branch_id', None):
    #        branch_id = kwargs['context']['branch_id']
    #        partner = Branch.objects.get(pk=branch_id).partner
    #        self.fields['employees'].queryset = Employee.objects.filter(partner=partner)

    #def to_representation(self, instance):
    #    rep = super().to_representation(instance)
    #    rep['employees'] = [{'id': emp.user_id, 'name': str(emp)} for emp in instance.employees.all()]
    #    return rep


class BranchSerializerForOwner(BranchSerializer):
    """
    Branch serializer for owner use that automatically assigns the authenticated user's owned partner to the branch.

    Attributes: Meta
        model (`django.db.models.Model`): `Branch` model to serialize.
        exclude (List): `['partner']` <br>
            all fields of the model to serialize except `partner`.

    Methods:
        create: Custom creation logic to assign the partner field based on the request's user.
    """
    class Meta:
        model = Branch
        fields = '__all__'
        read_only_fields = ['partner']

    def create(self, validated_data):
        """
        Custom creation logic to assign the partner field based on the request's user.

        Args:
            validated_data (dict): The raw validated data.

        Returns:
            (Branch): The newly created Branch instance.
        """
        request = self.context['request']
        validated_data['partner'] = request.user.owned_partner
        return super().create(validated_data)
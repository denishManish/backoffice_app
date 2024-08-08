from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.utils import model_meta
from drf_writable_nested.mixins import UniqueFieldsMixin
from drf_writable_nested.serializers import WritableNestedModelSerializer
from django.utils.translation import gettext_lazy as _

from .models import User, GroupDescription


#class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
#    def validate(self, attrs):
#        data = super().validate(attrs)

        # Add custom logic for blacklist old tokens or smth else

#        return data

#    @classmethod
#    def get_token(cls, user):
#        token = super().get_token(user)

        # Add custom claims
        # token['email'] = user.email
        
#        return token
    
class UserSerializer(UniqueFieldsMixin, serializers.ModelSerializer):
    """
    Serializer for User model with unique field handling (UniqueFieldsMixin) that includes custom validation for groups.

    Attributes:
        groups (PrimaryKeyRelatedField): __ManyToManyField from `Group` model__ <br>
            List of user's groups.
            Accessible as `groups`, accessible in query as `group`.
        
    Attributes: Meta
        model (`django.db.models.Model`): `User` model to serialize.
        exclude (List): `['username', 'user_permissions']` <br>
            all fields of the model to serialize except `username`, `user_permissions`.
        read_only_fields (List): 
            all fields of the model to serialize except the next: <br>
            `id`, `public_id`, `last_login`, `date_joined`, `is_active`, `is_staff`, `is_superuser`.
        extra_kwargs (dict): Additional keyword arguments for fields configuration. <br>
            Makes `password` field write-only and optional.

    Methods:
        validate_groups: 
            Validate that the user is assigned to no more than one group.
        create: 
            Create a new User instance using the provided validated data and handling `is_superuser` parameter.
        update: 
            Update an existing User instance using the provided validated data and handling `is_superuser` parameter.
        to_representation: 
            Include detailed representation of user's groups.
    """
    #groups = serializers.PrimaryKeyRelatedField(many=True, queryset=Group.objects.all(), allow_null=True, required=False)

    GroupChoices = [
        ('teacher', _('teacher')),
        ('owner', _('owner')),
    ]

    group = serializers.ChoiceField(choices=GroupChoices, write_only=True)

    class Meta:
        model = User
        exclude = ['username', 'user_permissions', 'groups']
        read_only_fields = ('id', 'public_id', 'last_login', 'date_joined', 'is_active', 'is_staff', 'is_superuser')
        extra_kwargs = {'password': {'write_only': True, 'required': False}}
    
    def validate_groups(self, value):
        """
        Validates that the user is assigned to no more than one group.

        Args:
            value (list): List of groups assigned to the user.

        Returns:
            (list): The validated group data.

        Raises:
            ValidationError: If more than one group is assigned.
        """
        if value and len(value) != 1:
            raise serializers.ValidationError("User can't have more than one group.")
        return value
    
    def create(self, validated_data):
        """
        Creates a new User instance using the provided validated data.  <br>
        This method manages many-to-many relations, specifically for 'groups'. It ensures that if a user is assigned
        to the 'superuser' group, the 'is_superuser' flag is set to True. Other User fields are set from 'validated_data'.

        Args:
            validated_data (dict): Dictionary containing all validated data necessary for user creation.

        Returns:
            (User): Newly created User instance.
        """
        ModelClass = self.Meta.model

        info = model_meta.get_field_info(ModelClass)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in validated_data):
                many_to_many[field_name] = validated_data.pop(field_name)
                #if field_name == "groups" and Group.objects.get(name='superuser') in many_to_many[field_name]:
                #    validated_data['is_superuser'] = True

        group_name = validated_data.pop('group', None)
        if group_name and group_name == 'superuser':
            validated_data['is_superuser'] = True

        instance = User.objects.create_user(**validated_data)

        if group_name:
            instance.groups.add(Group.objects.get(name=group_name))

        if many_to_many:
            for field_name, value in many_to_many.items():
                field = getattr(instance, field_name)
                field.set(value)

        return instance
    
    def update(self, instance, validated_data):
        """
        Update an existing User instance. <br>
        Manages updates to many-to-many fields and ensures proper handling of user privileges based on group membership.
        If the user is part of the 'superuser' group, the 'is_superuser' attribute is updated accordingly. Email changes
        are normalized to lowercase and passwords are set securely. Other fields are updated based on 'validated_data'.

        Args:
            instance (User): The existing User instance to be updated.
            validated_data (dict): Dictionary containing all new data for updates.

        Returns:
            (User): The updated User instance.
        """
        info = model_meta.get_field_info(instance)
        m2m_fields = []

        email = validated_data.get('email')
        if email and email.lower() == instance.email.lower():
            validated_data.pop('email', None)

        #groups = validated_data.get('groups')
        #if groups:
        #    if Group.objects.get(name='superuser') in groups:
        #        validated_data['is_superuser'] = True
        #    else:
        #        validated_data['is_superuser'] = False
        
        group_name = validated_data.pop('group', None)
        if group_name:
            if group_name == 'superuser':
                validated_data['is_superuser'] = True
            instance.groups.clear()
            instance.groups.add(Group.objects.get(name=group_name))

        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                if attr == 'password':
                    instance.set_password(value)
                else:
                    if attr == 'email':
                        value = value.lower()
                    setattr(instance, attr, value)
                    
        instance.save()

        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            field.set(value)

        return instance
    
    def to_representation(self, instance):
        """
        Convert a User instance into a dictionary format that can be serialized. <br>
        Extends the base representation to include a detailed representation of the user's groups. Each group is
        represented by its 'id' and 'name', providing a readable format for clients. <br>
        Translate the 'gender' field by the language of the request. Default is 'en'. 

        Args:
            instance (User): The User instance to be serialized.

        Returns:
            (dict): A dictionary representing the serialized User instance.
        """
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        first_group = instance.groups.first()
        if first_group:
            representation['group'] = _(first_group.name)
        else:
            representation['group'] = None
        #representation['groups'] = [{'id': group.id, 'name': _(group.name)} for group in instance.groups.all()]
        return representation


class GroupDescriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for GroupDescription model.

    Attributes: Meta
        model (`django.db.models.Model`): `Branch` model to serialize.
        fields (List): `['description']` <br>
            To serialize only `description` field.
    """
    class Meta:
        model = GroupDescription
        fields = ['description']


class GroupSerializer(WritableNestedModelSerializer):
    """
    Serializer for Group model with nested GroupDescription serialization.

    Attributes:
        group_description (GroupDescriptionSerializer):
            Serializer for the GroupDescription model.
        permissions (PrimaryKeyRelatedField): __ManyToManyField from `Permission` model__ <br>
            List of permissions assigned to the group. <br>
            Accessible as `permissions`, accessible in query as `permission`.

    Attributes: Meta
        model (`django.db.models.Model`): `Group` model to serialize.
        fields (List): `__all__` <br>
            all fields of the model to serialize.

    Methods:
        to_representation: Include detailed representation of group's permissions.
    """
    group_description = GroupDescriptionSerializer(source='description')
    permissions = serializers.PrimaryKeyRelatedField(many=True, queryset=Permission.objects.all(), allow_null=True, required=False)
    class Meta:
        model = Group
        fields = '__all__'

    def to_representation(self, instance):
        """
        Convert a Group instance into a dictionary format that can be serialized. <br>
        Extends the base representation to include a detailed representation of the group's permissions. Each permission is
        represented by its string representation, providing a readable format for clients.

        Args:
            instance (Group): The Group instance to be serialized.

        Returns:
            (dict): A dictionary representing the serialized Group instance.
        """
        representation = super().to_representation(instance)
        representation['name'] = _(instance.name)
        representation['permissions'] = [str(permission) for permission in instance.permissions.all()]
        return representation


class PermissionSerializer(serializers.ModelSerializer):
    """
    Serializer for Permission model.

    Attributes: Meta
        model (`django.db.models.Model`): `Permission` model to serialize.
        fields (List): `__all__` <br>
            all fields of the model to serialize.
    """
    class Meta:
        model = Permission
        fields = '__all__'
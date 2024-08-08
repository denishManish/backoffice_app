from rest_framework import serializers

from .models import Course, Category, Lesson
from partner_management.models import Employee


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for the Course model that ensures relationships with teachers and lessons, 
    also validate that a course's category includes all it's parent categories.

    Attributes:
        teachers (PrimaryKeyRelatedField): __ManyToManyField from Employee model__ <br>
            Teachers that have access for this course. <br>
            Accessible as `teachers`, accessible in query as `teacher`.
        lessons (PrimaryKeyRelatedField): __ManyToManyField from Lesson model__ <br>
            Lessons that are part of this course. <br>
            Accessible as `lessons`, accessible in query as `lesson`.
    
    Attributes: Meta
        model (`django.db.models.Model`): `Course` model to serialize.
        fields (List): `__all__` <br>
            all fields of the model to serialize.

    Methods:
        validate_categories: 
            Validates category selections to ensure parent categories are included automatically.
        to_representation: 
            Translates the 'status' field.
    """
    teachers = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Employee.objects.filter(user__groups__name="teacher"), 
        allow_null=True, 
        required=False
    )   
    lessons = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Lesson.objects.all(), 
        allow_null=True,
        required=False
    )   
    class Meta:
        model = Course
        fields = '__all__'

    def validate_categories(self, value):
        """
        Ensures that all parent categories of a selected category are automatically included in the course.

        Parameters:
            value (List): List of categories selected for the course.
        
        Returns:
            (List): List of categories including all hierarchical parents.
        """
        validated_categories = set(value)
        for category in value:
            while category.parent:
                validated_categories.add(category.parent)
                category = category.parent
        return list(validated_categories)
    
    def to_representation(self, instance):
        """
        Convert a Course instance into a dictionary format that can be serialized. <br>
        Translate the 'status' field by the language of the request. Default is 'en'. <br>
        Changes the 'categories' field to a list of category names.

        Args:
            instance (Course): The Course instance to be serialized.

        Returns:
            (dict): A dictionary representing the serialized Course instance.
        """
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        representation['categories'] = [category.name for category in instance.categories.all()]
        return representation

class CourseSerializerUpdateTeachers(serializers.ModelSerializer):
    """
    Serializer to only update teachers of a course. <br>
    Uses for users with 'owner' group.

    Attributes:
        teachers (PrimaryKeyRelatedField): __ManyToManyField from Employee model__ <br>
            Teachers that have access for this course. <br>
            Accessible as `teachers`, accessible in query as `teacher`.
    
    Attributes: Meta
        model (`django.db.models.Model`): `Course` model to serialize.
        fields (List): `['teachers']` <br>
            To serialize only `teachers` field.
    """
    teachers = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Employee.objects.filter(user__groups__name="teacher"), 
        allow_null=True, 
        required=False
    )
    class Meta:
        model = Course
        fields = ['teachers']


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model. <br>
    Handles serialization and deserialization of Category instances.

    Attributes: Meta
        model (`django.db.models.Model`): `Category` model to serialize.
        fields (List): `__all__` <br>
            all fields of the model to serialize.
    """
    class Meta:
        model = Category
        fields = '__all__'


class LessonSerializer(serializers.ModelSerializer):
    """
    Serializer for the Lesson model. <br>
    Handles serialization and deserialization with specific validation for media files associated with lessons.

    Attributes: Meta
        model (`django.db.models.Model`): `Lesson` model to serialize.
        fields (List): `__all__` <br>
            all fields of the model to serialize.

    Methods:
        validate_presentation: 
            Validates the file type of the presentation ensuring it is a `.pptx` file.
        validate_additional_file: 
            Validates the file type of additional materials ensuring they are either `.pdf` or `.zip` files.
    """
    class Meta:
        model = Lesson
        fields = '__all__'

    def validate_presentation(self, value):
        """
        Validates that the uploaded presentation file has a .pptx or .pdf extension.

        Parameters:
            value (UploadedFile): File uploaded as presentation of the lesson.
        
        Returns:
            (UploadedFile): Validated presentation file.

        Raises:
            ValidationError: If the file is not a `.pptx` or `.pdf` file.
        """
        if value and not (value.name.endswith('.pptx') or value.name.endswith('.pdf')):
            raise serializers.ValidationError("Only .pptx or .pdf files are allowed for presentations.")
        return value

    def validate_additional_file(self, value):
        """
        Validates that the uploaded additional file has a .pdf or .zip extension.

        Parameters:
            value (UploadedFile): File uploaded as additional file of the lesson.
        
        Returns:
            (UploadedFile): Validated additional file of the lesson.

        Raises:
            ValidationError: If the file is not a `.pdf` or `.zip` file.
        """
        if value and not (value.name.endswith('.pdf') or value.name.endswith('.zip')):
            raise serializers.ValidationError("Only .pdf or .zip files are allowed as additional file.")
        return value

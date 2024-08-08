from django.db.models import Q

from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Course, Category, Lesson
from .serializers import (
    CourseSerializer, 
    CategorySerializer, 
    LessonSerializer, 
    CourseSerializerUpdateTeachers,
)


class CourseViewSet(viewsets.ModelViewSet):
    """
    Viewset to manage courses.

    Attributes:
        parser_classes (tuple): Parsers for JSON, multipart, and form data.

    Methods: 
        get_serializer_class: 
            Determines the serializer class based on the group and action.
        get_queryset: 
            Customizes the queryset based on user group and multiple filters like search, status, category, and age.
    """
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_serializer_class(self):
        """
        Determines the serializer class based on the user's group and action being performed.

        Returns:
            CourseSerializer (ModelSerializer): Default.
            CourseSerializerUpdateTeachers (ModelSerializer): 
                For `owner` user on `update` and `partial_update` actions. <br>
                Created to ensure `owner` can't change any information of the course except list of teachers that have access to it.
        """
        if self.request.user.groups.filter(name='owner').exists() and self.action in ['update', 'partial_update']:
            return CourseSerializerUpdateTeachers
        return CourseSerializer

    def get_queryset(self):
        """
        Customizes the queryset retrieval for courses based on user group and filters. <br>
        If the user is a teacher, it will return lessons filtered to those they have access to.

        Attributes: Filters
            teacher (int): Filters courses by teacher id to ones that they have access to.
            search (str): Filters courses by name. <br> Case-insensitive.
            status (str): Filters courses by their status.
            category (str): Filters courses by category. <br> Case-insensitive.
            age (int): Filters courses checking if age in the course's age range.

        Examples:
            ```
            /?status=hidden
            /?search=Курс 1&status=active&category=Byte&age=18
            ```

        Returns:
            (QuerySet): A filtered queryset of Course objects.
        """
        queryset = Course.objects.all().order_by('id')

        if self.request.user.groups.filter(name='teacher').exists():
            queryset = queryset.filter(teacher__user=self.request.user)

        teacher = self.request.query_params.get('teacher', None)
        search = self.request.query_params.get('search', None)
        status = self.request.query_params.get('status', None)
        category = self.request.query_params.get('category', None)
        age = self.request.query_params.get('age', None)

        if teacher:
            queryset = queryset.filter(teacher=teacher)
        if search:
            queryset = queryset.filter(name__icontains=search)
        if status:
            queryset = queryset.filter(status=status)
        if category:
            queryset = queryset.filter(categories__name__icontains=category)
        if age:
            queryset = queryset.filter(Q(min_age__lte=age) & Q(max_age__gte=age))

        return queryset
    

class CategoryViewSet(viewsets.ModelViewSet):
    """
    Viewset to manage categories.

    Attributes:
        queryset (QuerySet): Categories ordered by their ID.
        serializer_class (ModelSerializer): `CategorySerializer`.
    """
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer


class LessonViewSet(viewsets.ModelViewSet):
    """
    Viewset to manage lessons.

    Attributes:
        serializer_class (ModelSerializer): `LessonSerializer`.
        parser_classes (tuple): Parsers for JSON, multipart, and form data.

    Methods:
        get_queryset: 
            Customizes the queryset to show only lessons associated with the current user's courses.
    """
    serializer_class = LessonSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
        """
        Retrieves a customized queryset of lessons. <br>
        If the user is a teacher, it will return lessons filtered to those they have access to.

        Attributes: Filters
            course_id (int): Filters lessons by course id.

        Examples:
            ```
            /?course_id=1
            ```

        Returns:
            (QuerySet): A filtered queryset of Lesson objects.
        """
        queryset = Lesson.objects.all().order_by('course')

        if self.request.user.groups.filter(name='teacher').exists():
            queryset = queryset.filter(course__teacher__user=self.request.user)

        course_id = self.request.query_params.get('course_id', None)

        if course_id:
            queryset = queryset.filter(course=course_id)

        return queryset

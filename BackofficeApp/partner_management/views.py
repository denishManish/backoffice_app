from datetime import datetime
from django.db.models.query import prefetch_related_objects
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Partner, Employee, Branch
from .serializers import *
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser  


class PartnerViewSet(viewsets.ModelViewSet):
    """
    Viewset to manage partners.

    Methods:
        get_serializer_class:
            Determines the serializer class based on the action and user role.
        get_queryset:
            Customizes the queryset based on user group and multiple filters like search, status and date.
    """
    def get_queryset(self):
        """
        Customizes the queryset retrieval for partners based on user group and filters, ordered by their creation date. <br>
        If the user is a teacher, it will return partner filtered to only that user is part of. <br>
        If the user is a owner, it will return partner filtered to only that user owns.

        Attributes: Filters
            search (str): Filters partners by name or legal entity. <br> Case-insensitive.
            status (str): Filters partners by their status.
            date (str): Filters partners by the date of creation.

        Examples:
            ```
            /?date=2022-01-01
            /?search=Партнер 1&status=active
            ```

        Returns:
            (QuerySet): A customized queryset of Partner objects.
        """
        queryset = Partner.objects.all().order_by('-creating_date')

        if self.request.user.groups.filter(name='teacher').exists():
            queryset = queryset.filter(employee__user=self.request.user)
        elif self.request.user.groups.filter(name='owner').exists():
            queryset = queryset.filter(owner=self.request.user)

        search = self.request.query_params.get('search', None)
        status = self.request.query_params.get('status', None)
        date_str = self.request.query_params.get('date', None)

        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(legal_entity__icontains=search))
        if status:
            queryset = queryset.filter(status=status)
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            queryset = queryset.filter(creating_date=date)

        return queryset

    def get_serializer_class(self):
        """
        Determines the serializer class based on the action being performed.

        Returns:
            PartnerSerializer (ModelSerializer): For actions `create`, `update`, `partial_update`, `destroy`.
            PartnerDetailSerializer (ModelSerializer): For actions `list`, `retrieve`.
        """
        if self.action in ['list', 'retrieve']:
            return PartnerDetailSerializer
        return PartnerSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    Viewset to manage employees.

    Attributes:
        parser_classes (tuple): Parsers for JSON, multipart, and form data.

    Methods:
        get_queryset: 
            Customizes the queryset based on user group and various filters like partner_id, search, status, and group.
        get_serializer_class: 
            Determines the serializer class based on the user's group.
        update: 
            Custom update logic that helps to update related to employee user instance.
        destroy: 
            Custom destroy method to delete both employee and related user.
    """
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_serializer_class(self):
        """
        Determines the serializer class based on the user's group.

        Returns:
            EmployeeSerializer (ModelSerializer): Default.
            EmployeeSerializerForOwner (ModelSerializer): If the user belongs to the 'owner' group.
        """
        if self.request.user.groups.filter(name='owner').exists():
            return EmployeeSerializerForOwner
        return EmployeeSerializer

    def get_queryset(self):
        """
        Customizes the queryset retrieval for employees based on user roles and filters. <br>
        If the user is a teacher, it will return filtered employees from the same partner.
        If the user is an owner, it will return filtered employees from their partner instance.

        Attributes: Filters
            partner_id (int): Filters employees by the partner id.
            course_id (int): Filters employees by the course id.
            search (str): Filters employees by user's first name, last name, patronymic or email. <br> Case-insensitive.
            status (str): Filters employees by their status.
            group (str): Filters employees by their group membership.

        Examples:
            ```
            /?partner_id=2
            /?search=петр овечкин&status=active
            ```

        Returns:
            (QuerySet): A filtered queryset of Employee objects.
        """
        queryset = Employee.objects.all().order_by('user_id')

        if self.request.user.groups.filter(name='teacher').exists():
            queryset = queryset.filter(partner=self.request.user.employee.partner)
        elif self.request.user.groups.filter(name='owner').exists():
            queryset = queryset.filter(partner=self.request.user.owned_partner)

        partner_id = self.request.query_params.get('partner_id', None)
        course_id = self.request.query_params.get('course_id', None)
        search = self.request.query_params.get('search', None)
        status = self.request.query_params.get('status', None)
        group = self.request.query_params.get('group', None)

        if partner_id:
            queryset = queryset.filter(partner__id=partner_id)
        if course_id:
            queryset = queryset.filter(courses__id=course_id)
        if search:
            search_terms = search.split()
            for term in search_terms:
                queryset = queryset.filter(
                    Q(user__first_name__icontains=term) | 
                    Q(user__last_name__icontains=term) | 
                    Q(user__patronymic__icontains=term) |
                    Q(user__email__icontains=term)
                )
        if status:
            queryset = queryset.filter(status=status)
        if group:
            queryset = queryset.filter(user__groups__name=group)

        return queryset
    
    def update(self, request, *args, **kwargs):
        """
        Custom update logic that handles related user data. <br>
        `user.id` is taken from URL parameters and copied to request's data copy to ensure correct user update. <br>
        That way, nested user serializer doesn't create a new user instance but just update it.

        Args:
            request (Request): The HTTP request object.
            *args (tuple): Positional arguments.
            **kwargs (dict): Keyword arguments. Includes 'pk' for partial updates.

        Returns:
            (Response): A Response object containing the serialized data.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        mutable_data = request.data.copy()
        mutable_data['user.id'] = kwargs.get('pk') 

        serializer = self.get_serializer(instance, data=mutable_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        queryset = self.filter_queryset(self.get_queryset())
        if queryset._prefetch_related_lookups:
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance,
            # and then re-prefetch related objects
            instance._prefetched_objects_cache = {}
            prefetch_related_objects([instance], *queryset._prefetch_related_lookups)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Custom destroy method to delete both the employee and related user data.

        Args:
            request (Request): The HTTP request object.
            *args (tuple): Positional arguments.
            **kwargs (dict): Keyword arguments.

        Returns:
            (Response): A Response object with HTTP status indicating the outcome.
        """
        employee = self.get_object()
        user = employee.user
        #employee.delete()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class BranchViewSet(viewsets.ModelViewSet):
    """
    Viewset to manage branches.

    Methods:
        get_queryset: 
            Customizes the queryset of Branches ordered by their opening date based on user group and filters.
        get_serializer_class: 
            Determines the serializer class based on the user's group.
    """

    #that's for filtering employees for branch in serializer
    #def get_serializer_context(self):
    #    context = super().get_serializer_context()
    #    if 'pk' in self.kwargs:
    #        context['branch_id'] = self.kwargs['pk']
    #    return context
    
    def get_serializer_class(self):
        """
        Determines the serializer class based on the user's group.

        Returns:
            BranchSerializer (ModelSerializer): Default.
            BranchSerializerForOwner (ModelSerializer): If the user belongs to the 'owner' group.
        """
        if self.request.user.groups.filter(name='owner').exists():
            return BranchSerializerForOwner
        return BranchSerializer

    def get_queryset(self):
        """
        Customizes the queryset retrieval for branches based on user roles and filters. <br>
        If the user is a teacher, it will return filtered branches from the same partner.
        If the user is an owner, it will return filtered branches from their partner instance.

        Attributes: Filters
            partner_id (str): Filters branches by partner id.
            search (str): Filters branches by name. <br> Case-insensitive.
            status (str): Filters branches by their status.
            date (str): Filters branches by the date of opening.

        Examples:
            ```
            /?date=2022-01-01
            /?search=Филиал 1&status=active
            ```

        Returns:
            (QuerySet): A filtered queryset of Branches objects.
        """
        queryset = Branch.objects.all().order_by('-opening_date')

        if self.request.user.groups.filter(name='teacher').exists():
            queryset = queryset.filter(partner=self.request.user.employee.partner)
        elif self.request.user.groups.filter(name='owner').exists():
            queryset = queryset.filter(partner=self.request.user.owned_partner)

        partner_id = self.request.query_params.get('partner_id', None)
        search = self.request.query_params.get('search', None)
        status = self.request.query_params.get('status', None)
        date_str = self.request.query_params.get('date', None)

        if partner_id:
            queryset = queryset.filter(partner__id=partner_id)
        if search:
            queryset = queryset.filter(name__icontains=search)
        if status:
            queryset = queryset.filter(status=status)
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            queryset = queryset.filter(opening_date=date)

        return queryset
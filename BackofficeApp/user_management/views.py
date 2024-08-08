from datetime import datetime

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, Permission
from rest_framework import viewsets, status
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from .models import User
from .serializers import GroupSerializer, UserSerializer, PermissionSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Handles the obtaining pair of tokens via HTTP POST request based on 'email' and 'password'. <br>
    Sets tokens in cookies with secure settings. <br>

    Methods:
        post: Processes the obtaining tokens request.
    """
    def post(self, request, *args, **kwargs):
        """
        Processes the POST request to obtain pair of tokens. <br>
        Sets tokens in cookies with settings `httponly`, `secure(in prod)`, `samesite='Strict'`, `expires`, `path`. <br>
        For access_token `path=/api` to only send it in API requests. <br>
        For refresh_token `path=/auth` to only send it in auth requests to get a new access token.

        Args:
            request (Request): The Django REST framework request object containing 'email' and 'password'.
            *args (tuple): Positional arguments.
            **kwargs (dict): Keyword arguments.

        Returns:
            (Response): 
                HTTP response indicating success or failure of obtaining tokens. <br>
                401 HTTP response for invalid credentials. <br>
                200 HTTP response for a successful obtaining tokens stored in cookies.
        """
        response = super().post(request, *args, **kwargs)
        tokens = response.data
        
        access_expiration = datetime.now() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
        refresh_expiration = datetime.now() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
        
        response.set_cookie(
            key='access_token',
            value=tokens['access'],
            httponly=True,
            secure=not settings.DEBUG,
            samesite='None',
            expires=access_expiration,
            path='/api'
        )
        response.set_cookie(
            key='refresh_token',
            value=tokens['refresh'],
            httponly=True,
            secure=not settings.DEBUG,
            samesite='None',
            expires=refresh_expiration,
            path='/auth'
        )
        
        response.data = {"detail": "Tokens set in cookies"}
        
        return response


class CustomTokenRefreshView(TokenRefreshView):
    """
    Handles the refreshing of access tokens via HTTP POST request. <br>
    Uses the refresh token stored in cookies. <br>

    Methods:
        post: Processes the refreshing tokens request.
    """
    def post(self, request, *args, **kwargs):
        """
        Processes the POST request to refresh the access token. <br>
        Uses the refresh token stored in cookies and sets the new access token in cookies with 
            settings `httponly`, `secure(in prod)`, `samesite='Strict'`, `expires`, `path=/api`. <br>

        Args:
            request (Request): The Django REST framework request object.
            *args (tuple): Positional arguments.
            **kwargs (dict): Keyword arguments.

        Returns:
            Response:
                HTTP response indicating success or failure of refreshing the token. <br>
                401 HTTP response for invalid or missing refresh token. (`raise InvalidToken(e.args[0])`) <br>
                200 HTTP response for a successful token refresh with new access token in cookies.
        """
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                raise InvalidToken("No refresh token provided")

            data = {'refresh': refresh_token}
            request._full_data = data

            response = super().post(request, *args, **kwargs)
            tokens = response.data

            access_expiration = datetime.now() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
            
            response.set_cookie(
                key='access_token',
                value=tokens['access'],
                httponly=True,
                secure=not settings.DEBUG,
                samesite='None',
                expires=access_expiration,
                path='/api'
            )
            
            response.data = {"detail": "Tokens set in cookies"}
            
            return response
        
        except InvalidToken as e:
            raise InvalidToken(e.args[0])


class SessionLoginAPIView(APIView):
    """
    Handles the session login via HTTP POST request based on 'email' and 'password'. <br>

    Attributes:
        permission_classes (list): `[permissions.AllowAny]` <br> 
            Specifies that any user can make login requests.

    Methods:
        post: Processes the login request.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Processes the POST request to log a user in.

        Args:
            request (Request): The Django REST framework request object containing 'email' and 'password'.

        Returns:
            (Response): 
                HTTP response indicating success or failure of login. <br>
                401 HTTP response for invalid credentials. <br>
                200 HTTP response for a successful login.
        """
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        login(request, user)
        return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)


class SessionLogoutAPIView(APIView):
    """
    Handles the session logout via HTTP POST request. <br>.

    Attributes:
        permission_classes (list): `[permissions.IsAuthenticated]` <br> 
            Specifies that only authenticated users can make logout requests.

    Methods:
        post: Processes the logout request.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Processes the POST request to log a user out.

        Args:
            request (Request): The DRF request object.

        Returns:
            (Response): 
                HTTP response indicating success of logout. <br>
                200 HTTP response indicating successful logout.
        """
        logout(request)
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """
    Viewset to manage users.

    Attributes:
        queryset (QuerySet): Users ordered by the date they joined.
        serializer_class (ModelSerializer): `UserSerializer`.
        parser_classes (tuple): Parsers for JSON, multipart, and form data.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)


class GroupPermissionsView(APIView):
    """
    API endpoint that allows users to view the group they are part of, 
        permissions of that group and partner_id associated with the user. <br>
        For `superuser` partner_id is None.

    Attributes:
        permission_classes (list): `[permissions.IsAuthenticated]` <br> 
            Specifies that only authenticated users can make request.
    
    Methods:
        get: Returns the group, permissions and partner_id of the logged-in user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Args:
            request (Request): The HTTP request object.

        Returns:
            (Response): 
                200 HTTP response if successful. Contains the group, permissions, partner_id for the logged-in user. <br>
                404 HTTP response if the user is not part of any group.
        """
        user_group = request.user.groups.first()
        if user_group:
            partner_id = None
            if user_group.name == 'owner':
                partner_id = request.user.owned_partner.id
            elif user_group.name == 'teacher':
                partner_id = request.user.employee.partner.id
            data = {
                'group_name': user_group.name,
                'permissions': [perm.codename for perm in user_group.permissions.all()],
                'partner_id': partner_id,
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'User is not part of any group'}, status=status.HTTP_404_NOT_FOUND)


class GroupViewSet(viewsets.ModelViewSet):
    """
    Viewset to manage groups.

    Attributes:
        queryset (Queryset)): Groups ordered by their name.
        serializer_class (ModelSerializer): `GroupSerializer`.
    """
    queryset = Group.objects.all().order_by('name')
    serializer_class = GroupSerializer


class PermissionViewSet(viewsets.ModelViewSet):
    """
    Viewset to manage permissions.

    Attributes:
        serializer_class (ModelSerializer): `PermissionSerializer`.

    Methods:
        get_queryset: Filtered queryset based on the name of the permission.
    """
    serializer_class = PermissionSerializer

    def get_queryset(self):
        """
        Retrieve a queryset of Permission objects filtered by a search query.

        Attributes: Filters
            search (str): Filters permissions by name. <br> Case-insensitive.

        Examples:
            ```
            /?search=employee
            /?search=edit
            ```

        Returns:
            (QuerySet): A filtered queryset of Permission objects.
        """
        queryset = Permission.objects.all().order_by('content_type')

        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset

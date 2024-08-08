from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed


class CookiesJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication class that retrieves the JWT token from cookies.
    
    Methods:
        authenticate: Authenticates the request using the access token from cookies.
    """
    def authenticate(self, request):
        """
        Authenticates the request using the access token stored in cookies.

        This method overrides the default `authenticate` method to extract the
        access token from the cookies instead of the Authorization header.

        Args:
            request (Request): The Django REST framework request object.

        Returns:
            (tuple): A tuple containing the user and the validated token if authentication is successful.
            (None): If no access token is found in the cookies.

        Raises:
            AuthenticationFailed: If the token is invalid or any other authentication error occurs.
        """
        access_token = request.COOKIES.get('access_token')
        
        if access_token is None:
            return None
        
        try:
            validated_token = self.get_validated_token(access_token)
        except InvalidToken as e:
            raise AuthenticationFailed('Invalid token')

        return self.get_user(validated_token), validated_token

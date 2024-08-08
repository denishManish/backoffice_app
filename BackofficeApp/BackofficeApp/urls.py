from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from django.utils.translation import gettext_lazy as _

from user_management import views as user_views
from partner_management import views as partner_views
from course_management import views as course_views


# Router configuration to handle API endpoint registration.
router = routers.DefaultRouter()
router.register(r'users', user_views.UserViewSet, basename='user')
router.register(r'groups', user_views.GroupViewSet, basename='group')
router.register(r'permissions', user_views.PermissionViewSet, basename='permission')
router.register(r'partners', partner_views.PartnerViewSet, basename='partner')
router.register(r'employees', partner_views.EmployeeViewSet, basename='employee')
router.register(r'branches', partner_views.BranchViewSet, basename='branch')
router.register(r'courses', course_views.CourseViewSet, basename='course')
router.register(r'categories', course_views.CategoryViewSet, basename='category')
router.register(r'lessons', course_views.LessonViewSet, basename='lesson')

# URL patterns to route the different endpoints.
urlpatterns = (
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')), # for api auth only in development
    
    path('api/user-group-permissions/', user_views.GroupPermissionsView.as_view(), name='user_group_with_permissions'),

    #path('api/session/login/', user_views.SessionLoginAPIView.as_view(), name='session_login'),
    #path('api/session/logout/', user_views.SessionLogoutAPIView.as_view(), name='session_logout'),
    
    path('auth/token/', user_views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', user_views.CustomTokenRefreshView.as_view(), name='token_refresh'),
)
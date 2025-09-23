from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from library_service_auth.views import CreateCustomerView, ManageCustomerView

router = routers.DefaultRouter()

app_name = 'library_service_auth'

urlpatterns = [
    path("register/", CreateCustomerView.as_view(), name="create"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("me/", ManageCustomerView.as_view(), name="manage"),
]

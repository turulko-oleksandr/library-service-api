from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from library_service_users.views import CreateCustomerView, ManageCustomerView


app_name = 'library_service_users'

urlpatterns = [
    path("register/", CreateCustomerView.as_view(), name="create"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("me/", ManageCustomerView.as_view(), name="manage"),
]

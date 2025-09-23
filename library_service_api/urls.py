from django.urls import path, include
from rest_framework import routers

from library_service_api.views import BookViewSet
from library_service_auth.views import CreateCustomerView

app_name = "library_service_api"

router = routers.DefaultRouter()
router.register(r'books', BookViewSet)

urlpatterns = [path("", include(router.urls))]
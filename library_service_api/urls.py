from django.urls import path, include
from rest_framework import routers

from library_service_api.views import (BookViewSet,
                                       BorrowingViewSet,
                                       PaymentViewSet)

app_name = "library_service_api"

router = routers.DefaultRouter()
router.register(r'books', BookViewSet)
router.register(r'borrowings', BorrowingViewSet, basename='borrowings')
router.register(r'payments', PaymentViewSet, basename="payments")

urlpatterns = [path("", include(router.urls))]

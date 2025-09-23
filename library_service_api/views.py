from rest_framework import viewsets

from library_service_api.models import Book
from library_service_api.permissions import IsAdminOrIfAuthenticatedReadOnly
from library_service_api.serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    queryset = Book.objects.all()
    serializer_class = BookSerializer

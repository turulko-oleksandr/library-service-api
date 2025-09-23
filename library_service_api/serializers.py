from rest_framework.serializers import ModelSerializer
from library_service_api.models import Book


class BookSerializer(ModelSerializer):
    class Meta:
        model = Book
        fields = "__all__"
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from library_service_api.models import Book, Borrowing


class BookSerializer(ModelSerializer):
    class Meta:
        model = Book
        fields = "__all__"


class BorrowingSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    book = serializers.StringRelatedField(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        source="book",
        write_only=True
    )

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "book_id",
            "user",
        ]
        read_only_fields = ["id", "borrow_date", "user", "actual_return_date"]

    def create(self, validated_data):
        book = validated_data["book"]

        if book.inventory < 1:
            raise serializers.ValidationError(
                "This book is not available for borrowing."
            )
        book.inventory -= 1
        book.save()

        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

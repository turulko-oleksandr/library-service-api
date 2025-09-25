from django.db import transaction
from django.utils.timezone import now
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from library_service_api.models import Book, Borrowing
from library_service_api.permissions import IsAdminOrIfAuthenticatedReadOnly
from library_service_api.serializers import BookSerializer, BorrowingSerializer


class BookViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BorrowingViewSet(viewsets.ModelViewSet):
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]
    queryset = Borrowing.objects.all()
    filterset_fields = ["user", "actual_return_date"]

    def get_queryset(self):
        user = self.request.user
        queryset = Borrowing.objects.all()

        # Non-admin users see only their own borrowings
        if not user.is_staff:
            queryset = queryset.filter(user=user)

        # Filtering by query params
        user_id = self.request.query_params.get("user_id")
        if user_id and user.is_staff:
            queryset = queryset.filter(user_id=user_id)

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            if is_active.lower() in ["true", "1"]:
                queryset = queryset.filter(actual_return_date__isnull=True)
            elif is_active.lower() in ["false", "0"]:
                queryset = queryset.filter(actual_return_date__isnull=False)

        return queryset

    @action(detail=True, methods=["post"], url_path="return")
    def return_borrowing(self, request, pk=None):
        borrowing = self.get_object()

        if borrowing.actual_return_date:
            return Response(
                {"detail": "This borrowing has already been returned."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            book = Book.objects.select_for_update().get(id=borrowing.book.id)
            book.inventory += 1
            book.save(update_fields=["inventory"])

            borrowing.actual_return_date = now().date()
            borrowing.save(update_fields=["actual_return_date"])

        return Response(BorrowingSerializer(borrowing).data)

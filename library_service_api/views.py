import stripe
from django.db import transaction
from django.utils.timezone import now
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from library_service_api.models import Book, Borrowing, Payment
from library_service_api.permissions import IsAdminOrIfAuthenticatedReadOnly
from library_service_api.serializers import (BookSerializer,
                                             BorrowingSerializer,
                                             PaymentSerializer)
from library_service_api.services.payments_service import create_fine_payment
from library_service_api.services.telegram_service import send_telegram_message


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

    @action(
        detail=True,
        methods=["post"],
        url_name="return",
        url_path="return"
    )
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

        send_telegram_message(
            f"✅ Borrowing returned!\n\n"
            f"User: {borrowing.user}\n"
            f"Book: {borrowing.book}\n"
            f"Returned at: {borrowing.actual_return_date}"
        )

        fine_payment = None
        if borrowing.actual_return_date > borrowing.expected_return_date:
            days_late = (
                    borrowing.actual_return_date
                    - borrowing.expected_return_date
            ).days
            fine_amount = days_late * borrowing.book.daily_fee
            fine_payment = create_fine_payment(request, borrowing, fine_amount)

        response_data = BorrowingSerializer(borrowing).data
        if fine_payment:
            response_data["fine_payment"] = PaymentSerializer(
                fine_payment
            ).data

        return Response(response_data, status=status.HTTP_200_OK)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    queryset = Payment.objects.all()

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if not user.is_staff:
            qs = qs.filter(borrowing__user=user)
        return qs

    @action(
        detail=False,
        methods=["get"],
        url_name="success",
        url_path="success"
    )
    def success(self, request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response(
                {"detail": "session_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            payment = Payment.objects.get(session_id=session_id)
            if session.payment_status == "paid":
                payment.status = Payment.StatusChoices.PAID
                payment.save(update_fields=["status"])
            return Response(PaymentSerializer(payment).data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=["get"],
        url_name="cancel",
        url_path="cancel")
    def cancel(self, request):
        return Response({"detail": "Payment was cancelled or paused."})

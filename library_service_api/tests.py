from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from library_service_api.models import Book, Borrowing, Payment


BOOKS_URL = reverse("library_service_api:books-list")
BORROWINGS_URL = reverse("library_service_api:borrowings-list")
PAYMENTS_URL = reverse("library_service_api:payments-list")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class ModelTests(TestCase):
    def test_book_str(self):
        book = Book.objects.create(
            title="Test Book",
            author="Author",
            daily_fee=Decimal("2.50"),
            inventory=5,
            cover="SOFT"
        )
        self.assertEqual(str(book), book.title)

    def test_borrowing_str(self):
        user = create_user(email="user@example.com", password="testpass123")
        book = Book.objects.create(
            title="Test",
            author="Author",
            daily_fee=Decimal("1.00"),
            inventory=1
        )
        borrowing = Borrowing.objects.create(
            expected_return_date=date.today() + timedelta(days=3),
            book=book,
            user=user
        )
        self.assertIn("borrowed", str(borrowing))

    def test_payment_str(self):
        user = create_user(email="pay@example.com", password="pass12345")
        book = Book.objects.create(
            title="Payment Book",
            author="Auth",
            daily_fee=Decimal("1.00"),
            inventory=1
        )
        borrowing = Borrowing.objects.create(
            expected_return_date=date.today() + timedelta(days=2),
            book=book,
            user=user
        )
        payment = Payment.objects.create(
            borrowing=borrowing,
            session_url="http://test.com/session",
            session_id="abc123",
            money_to_pay=Decimal("5.00")
        )
        self.assertIn("Payment for borrowing ID", str(payment))


class BookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="test@example.com", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_books(self):
        Book.objects.create(
            title="Book1", author="Author1",
            daily_fee=Decimal("1.50"), inventory=2
        )
        res = self.client.get(BOOKS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 1)


class BorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="borrower@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.book = Book.objects.create(
            title="Borrowable Book",
            author="Auth",
            daily_fee=Decimal("3.00"),
            inventory=2
        )

    @patch("library_service_api.serializers.create_stripe_session")
    @patch("library_service_api.serializers.send_telegram_message")
    def test_create_borrowing_success(self, mock_telegram, mock_stripe):
        mock_stripe.return_value = MagicMock()
        payload = {
            "book_id": self.book.id,
            "expected_return_date": (
                    date.today() + timedelta(days=5)
            ).isoformat()
        }
        res = self.client.post(BORROWINGS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 1)  # inventory decreased
        mock_telegram.assert_called_once()

    def test_cannot_borrow_if_no_inventory(self):
        self.book.inventory = 0
        self.book.save()
        payload = {
            "book_id": self.book.id,
            "expected_return_date": (
                    date.today() + timedelta(days=5)
            ).isoformat()
        }
        res = self.client.post(BORROWINGS_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("library_service_api.views.create_fine_payment")
    @patch("library_service_api.views.send_telegram_message")
    def test_return_borrowing_creates_fine_if_late(
            self, mock_telegram, mock_fine
    ):
        borrowing = Borrowing.objects.create(
            expected_return_date=date.today() - timedelta(days=1),  # overdue
            book=self.book,
            user=self.user
        )

        mock_payment = Payment(
            borrowing=borrowing,
            money_to_pay=Decimal("10.00"),
            session_id="mock123",
            session_url="http://mock.url"
        )
        mock_fine.return_value = mock_payment

        url = reverse(
            "library_service_api:borrowings-return",
            args=[borrowing.id]
        )
        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        borrowing.refresh_from_db()
        self.book.refresh_from_db()
        self.assertIsNotNone(borrowing.actual_return_date)
        self.assertEqual(self.book.inventory, 3)  # inventory restored
        mock_fine.assert_called_once()


class PaymentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="payer@example.com", password="123pass")
        self.client.force_authenticate(user=self.user)

        self.book = Book.objects.create(
            title="Book Pay",
            author="Auth",
            daily_fee=Decimal("2.00"),
            inventory=1
        )
        self.borrowing = Borrowing.objects.create(
            expected_return_date=date.today() + timedelta(days=2),
            book=self.book,
            user=self.user
        )
        self.payment = Payment.objects.create(
            borrowing=self.borrowing,
            session_url="http://test.com/s",
            session_id="sess123",
            money_to_pay=Decimal("10.00")
        )

    def test_list_payments_for_user(self):
        res = self.client.get(PAYMENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 4)

    @patch("library_service_api.views.stripe.checkout.Session.retrieve")
    def test_payment_success_marks_as_paid(self, mock_retrieve):
        mock_retrieve.return_value.payment_status = "paid"
        url = reverse("library_service_api:payments-success")
        res = self.client.get(url, {"session_id": self.payment.session_id})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.StatusChoices.PAID)

    def test_payment_success_without_session_id(self):
        url = reverse("library_service_api:payments-success")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_payment_cancel(self):
        url = reverse("library_service_api:payments-cancel")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("cancelled", res.data["detail"].lower())

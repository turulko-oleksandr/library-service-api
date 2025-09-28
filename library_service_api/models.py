from django.contrib.auth import get_user_model
from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    daily_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    inventory = models.PositiveIntegerField()
    COVER_CHOICES = (
        ("SOFT", "SOFT"),
        ("HARD", "HARD"),
    )
    cover = models.CharField(
        max_length=10,
        choices=COVER_CHOICES,
        default="SOFT"
    )

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title}"


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(
        "Book",
        on_delete=models.CASCADE,
        related_name="borrowings"
    )
    user = models.ForeignKey(
        get_user_model(),
        null=False,
        on_delete=models.CASCADE,
        related_name="borrowings"
    )

    class Meta:
        ordering = ["-borrow_date"]

    def __str__(self):
        return f"{self.user.email} borrowed {self.book.title}"


class Payment(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        EXPIRED = "EXPIRED", "Expired"

    class TypeChoices(models.TextChoices):
        PAYMENT = "PAYMENT", "Payment"
        FINE = "FINE", "Fine"

    status = models.CharField(
        max_length=8,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    type = models.CharField(
        max_length=7,
        choices=TypeChoices.choices,
        default=TypeChoices.PAYMENT
    )
    borrowing = models.ForeignKey(
        "Borrowing",
        on_delete=models.CASCADE,
        related_name="payments"
    )
    session_url = models.URLField(max_length=500)
    session_id = models.CharField(max_length=255, unique=True)
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return (f"Payment for borrowing ID: "
                f"{self.borrowing.id} "
                f"({self.get_status_display()})")

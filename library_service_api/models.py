from email.policy import default
from random import choices

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
        (1, 'HARD'),
        (0, 'SOFT')
    )
    cover = models.IntegerField(
        choices=COVER_CHOICES,
        default=0
    )

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

    def __str__(self):
        return f"{self.user.email} borrowed {self.book.title}"

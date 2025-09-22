from email.policy import default
from random import choices

from django.db import models

# Create your models here.
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


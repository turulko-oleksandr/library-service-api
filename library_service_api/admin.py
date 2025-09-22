from django.contrib import admin

from library_service_api.models import Book, Borrowing, Payment
from library_service_auth.models import Customer

# Register your models here.
admin.site.register(Book)
admin.site.register(Borrowing)
admin.site.register(Payment)

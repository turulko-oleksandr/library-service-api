import stripe
from django.urls import reverse
from library_service_api.models import Payment


def create_stripe_session(request, borrowing, amount, payment_type="PAYMENT"):
    """Create Stripe Session і Payment"""

    success_path = reverse("library_service_api:payments-success")
    success_url = (request.build_absolute_uri(success_path)
                   + "?session_id={CHECKOUT_SESSION_ID}")

    cancel_path = reverse("library_service_api:payments-cancel")
    cancel_url = request.build_absolute_uri(cancel_path)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Borrowing book: {borrowing.book.title}"
                    },
                    "unit_amount": int(amount * 100),
                },
                "quantity": 1,
            }
        ],
        success_url=success_url,
        cancel_url=cancel_url,
    )

    payment = Payment.objects.create(
        borrowing=borrowing,
        type=payment_type,
        status=Payment.StatusChoices.PENDING,
        money_to_pay=amount,
        session_id=session.id,
        session_url=session.url,
    )

    return payment


def create_fine_payment(request, borrowing, fine_amount):
    """Create Stripe Session & Payment for fines"""
    return create_stripe_session(
        request=request,
        borrowing=borrowing,
        amount=fine_amount,
        payment_type=Payment.TypeChoices.FINE,
    )

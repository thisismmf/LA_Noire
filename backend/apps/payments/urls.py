from django.urls import path
from .views import PaymentCreateView, PaymentReturnView, PaymentCallbackView

urlpatterns = [
    path("payments/create/", PaymentCreateView.as_view(), name="payment-create"),
    path("payments/return/", PaymentReturnView.as_view(), name="payment-return"),
    path("payments/callback/", PaymentCallbackView.as_view(), name="payment-callback"),
]

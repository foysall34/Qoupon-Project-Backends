import logging
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from mollie.api.client import Client
from .models import SubscriptionPlan, Subscription
from .serializers import SubscriptionPlanSerializer, SubscriptionSerializer
from food.models import Profile

logger = logging.getLogger(__name__)


def get_mollie_client():
    mollie = Client()
    mollie.set_api_key(settings.MOLLIE_API_KEY)
    return mollie


@api_view(["GET"])
@permission_classes([AllowAny])
def list_plans(request):
    """Return available subscription plans"""
    plans = SubscriptionPlan.objects.all()
    return Response(SubscriptionPlanSerializer(plans, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_subscription(request, plan_id):
    """Start Mollie subscription setup with initial payment"""
    user = request.user
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    mollie = get_mollie_client()
    user_profile = Profile.objects.get(user=user)

    try:
        # Ensure Mollie customer exists
        if not hasattr(user, "mollie_customer_id") or not user.mollie_customer_id:
            customer = mollie.customers.create({
                "name": user_profile.full_name,
                "email": user.email,
            })
            user.mollie_customer_id = customer.id
            user.save()
        else:
            customer = mollie.customers.get(user.mollie_customer_id)

        # ✅ Create first payment for mandate
        payment = customer.payments.create({
            "amount": {"currency": plan.currency, "value": f"{plan.amount:.2f}"},
            "description": f"Initial payment for {plan.name}",
            "sequenceType": "first",
            "redirectUrl": request.data.get("redirect_url"),
            "webhookUrl": request.build_absolute_uri("/subscription/webhook/mollie/"),
            "metadata": {"user_id": user.id, "plan_id": plan.id},
        })

        return Response({"checkout_url": payment.checkout_url}, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating subscription setup: {e}")
        return Response({"error": "Failed to start subscription"}, status=500)




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_subscription(request, subscription_id):
    """Cancel a Mollie subscription"""
    user = request.user
    subscription = get_object_or_404(Subscription, id=subscription_id, user=user)
    mollie = get_mollie_client()

    try:
        # Cancel via Mollie API
        customer = mollie.customers.get(subscription.mollie_customer_id)
        mollie_sub = customer.subscriptions.get(subscription.mollie_subscription_id)
        mollie_sub = mollie_sub.cancel()  # Mollie marks it as canceled

        # Update locally
        subscription.status = mollie_sub.status  # should be "canceled"
        subscription.cancel_date = timezone.now()
        subscription.save()

        return Response(
            {"message": "Subscription cancelled successfully", "subscription": SubscriptionSerializer(subscription).data},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Error cancelling subscription {subscription.id}: {e}")
        return Response({"error": "Failed to cancel subscription"}, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
def mollie_webhook(request):
    """Unified Mollie webhook handler"""
    mollie = get_mollie_client()
    mollie_id = request.data.get("id")
    
    if not mollie_id:
        return Response({"error": "Missing Mollie ID"}, status=400)

    logger.info(f"🔔 Webhook received: {mollie_id}")

    try:
        # Determine if this is a payment or subscription
        if mollie_id.startswith('tr_'):  # Payment ID
            return handle_payment_webhook(mollie, mollie_id)
        elif mollie_id.startswith('sub_'):  # Subscription ID
            return handle_subscription_webhook(mollie, mollie_id)
        else:
            logger.warning(f"Unknown Mollie ID format: {mollie_id}")
            return Response(status=200)
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return Response(status=200)


def handle_payment_webhook(mollie, payment_id):
    """Handle payment webhooks"""
    try:
        payment = mollie.payments.get(payment_id)
        metadata = payment.metadata or {}
        
        logger.info(f"💳 Payment {payment_id}: {payment.status}, sequence: {getattr(payment, 'sequence_type', 'N/A')}")
        
        # Only create subscription for successful first payments
        if getattr(payment, 'sequence_type', None) == "first" and payment.is_paid():
            user_id = metadata.get("user_id")
            plan_id = metadata.get("plan_id")
            
            if user_id and plan_id:
                create_subscription_after_payment(user_id, plan_id, payment.customer_id)
        
        return Response(status=200)
        
    except Exception as e:
        logger.error(f"Payment webhook error: {e}")
        return Response(status=200)


def handle_subscription_webhook(mollie, subscription_id):
    """Handle subscription webhooks"""
    try:
        subscription = Subscription.objects.filter(mollie_subscription_id=subscription_id).first()
        
        if subscription:
            customer = mollie.customers.get(subscription.mollie_customer_id)
            mollie_sub = customer.subscriptions.get(subscription_id)
            
            old_status = subscription.status
            subscription.status = mollie_sub.status
            
            if mollie_sub.status in ["canceled", "suspended"] and not subscription.cancel_date:
                subscription.cancel_date = timezone.now()
            
            subscription.save()
            logger.info(f"📝 Subscription {subscription.id} status: {old_status} -> {subscription.status}")
        else:
            logger.warning(f"No local subscription found for: {subscription_id}")
            
        return Response(status=200)
        
    except Exception as e:
        logger.error(f"Subscription webhook error: {e}")
        return Response(status=200)


def create_subscription_after_payment(user_id, plan_id, customer_id):
    """Create subscription after successful initial payment"""
    from django.contrib.auth import get_user_model
    from dateutil.relativedelta import relativedelta
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        plan = SubscriptionPlan.objects.get(id=plan_id)
        mollie = get_mollie_client()
        customer = mollie.customers.get(customer_id)

        # Convert to Mollie-compatible interval
        interval = str(plan.interval).strip().lower()
        
        # Calculate end_date based on interval
        start_date = timezone.now()
        if 'year' in interval:
            years = int(interval.split()[0])
            end_date = start_date + relativedelta(years=years)
        elif 'month' in interval:
            months = int(interval.split()[0])
            end_date = start_date + relativedelta(months=months)
        elif 'week' in interval:
            weeks = int(interval.split()[0])
            end_date = start_date + relativedelta(weeks=weeks)
        else:
            # Default to 1 month
            end_date = start_date + relativedelta(months=1)
        
        # Convert years to months for Mollie API
        if 'year' in interval:
            years = int(interval.split()[0])
            mollie_interval = f"{years * 12} months"
        else:
            mollie_interval = interval

        logger.info(f"🔍 Using Mollie interval: '{mollie_interval}', End date: {end_date}")

        # Check for existing subscription
        if Subscription.objects.filter(user=user, plan=plan, status__in=["active", "pending"]).exists():
            logger.info(f"Subscription already exists for user {user.id}")
            return

        # Create Mollie subscription
        subscription = customer.subscriptions.create({
            "amount": {"currency": plan.currency, "value": f"{plan.amount:.2f}"},
            "interval": mollie_interval,
            "description": f"Subscription for {plan.name}",
            "webhookUrl": f"{settings.SITE_URL}/subscription/webhook/mollie/",
            "metadata": {"user_id": user.id, "plan_id": plan.id}
        })

        # Create local subscription record with calculated end_date
        Subscription.objects.create(
            user=user,
            plan=plan,
            mollie_customer_id=customer_id,
            mollie_subscription_id=subscription.id,
            status=subscription.status,
            start_date=start_date,
            end_date=end_date  # Next renewal date
        )
        
        logger.info(f"✅ Subscription created for user {user.id}: {subscription.id}, renews on: {end_date}")
        
    except Exception as e:
        logger.error(f"Error creating subscription after payment: {e}")
import os
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Depends
from bson import ObjectId
import stripe as stripe_lib

from database import db
from auth import get_current_user
from config import RAZORPAY_KEY_ID, SKRILL_MERCHANT_EMAIL, SKRILL_API_PASSWORD, razorpay_client, paypal_client
from models import PaymentCheckoutRequest, RazorpayOrderRequest, PayPalOrderRequest, SkrillPaymentRequest

from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
import razorpay as razorpay_mod

logger = logging.getLogger(__name__)
router = APIRouter(tags=["payments"])


# ---- Stripe ----

@router.post("/payments/checkout")
async def create_checkout_session(request: PaymentCheckoutRequest, user: dict = Depends(get_current_user)):
    booking = await db.bookings.find_one({"_id": ObjectId(request.booking_id)})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    stripe_lib.api_key = os.environ.get("STRIPE_API_KEY")
    session = stripe_lib.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price_data": {"currency": "usd", "unit_amount": int(booking["total_price"] * 100), "product_data": {"name": f"Booking {request.booking_id}"}}, "quantity": 1}],
        mode="payment",
        success_url=f"{request.origin_url}/booking-success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{request.origin_url}/booking-cancel",
        metadata={"booking_id": request.booking_id},
    )
    await db.payment_transactions.insert_one({"booking_id": request.booking_id, "session_id": session.id, "amount": booking["total_price"], "currency": "usd", "payment_status": "pending", "created_at": datetime.now(timezone.utc)})
    return {"url": session.url, "session_id": session.id}


@router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str):
    stripe_lib.api_key = os.environ.get("STRIPE_API_KEY")
    session = stripe_lib.checkout.Session.retrieve(session_id)
    payment_status = "paid" if session.payment_status == "paid" else session.payment_status

    await db.payment_transactions.update_one({"session_id": session_id}, {"$set": {"payment_status": payment_status}})
    if payment_status == "paid":
        tx = await db.payment_transactions.find_one({"session_id": session_id})
        if tx:
            await db.bookings.update_one({"_id": ObjectId(tx["booking_id"])}, {"$set": {"status": "confirmed", "payment_status": "paid"}})

    return {"session_id": session_id, "payment_status": payment_status, "amount_total": session.amount_total}


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    stripe_lib.api_key = os.environ.get("STRIPE_API_KEY")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    try:
        event = stripe_lib.Webhook.construct_event(body, signature, webhook_secret) if webhook_secret else json.loads(body)
        logger.info(f"Webhook received: {event.get('type', 'unknown')}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ---- Razorpay ----

@router.post("/payments/razorpay/create-order")
async def create_razorpay_order(request: RazorpayOrderRequest, user: dict = Depends(get_current_user)):
    if not razorpay_client:
        raise HTTPException(status_code=400, detail="Razorpay not configured")
    booking = await db.bookings.find_one({"_id": ObjectId(request.booking_id)})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    try:
        order = razorpay_client.order.create(data={"amount": int(request.amount * 100), "currency": request.currency, "payment_capture": 1, "notes": {"booking_id": request.booking_id}})
        await db.payment_transactions.insert_one({"booking_id": request.booking_id, "razorpay_order_id": order["id"], "amount": request.amount, "currency": request.currency, "payment_status": "created", "payment_method": "razorpay", "created_at": datetime.now(timezone.utc)})
        return {"order_id": order["id"], "amount": order["amount"], "currency": order["currency"], "key_id": RAZORPAY_KEY_ID}
    except Exception as e:
        logger.error(f"Razorpay order creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Payment order creation failed: {e}")


@router.post("/payments/razorpay/verify")
async def verify_razorpay_payment(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str):
    if not razorpay_client:
        raise HTTPException(status_code=400, detail="Razorpay not configured")
    try:
        razorpay_client.utility.verify_payment_signature({"razorpay_order_id": razorpay_order_id, "razorpay_payment_id": razorpay_payment_id, "razorpay_signature": razorpay_signature})
        await db.payment_transactions.update_one({"razorpay_order_id": razorpay_order_id}, {"$set": {"razorpay_payment_id": razorpay_payment_id, "payment_status": "paid", "verified_at": datetime.now(timezone.utc)}})
        tx = await db.payment_transactions.find_one({"razorpay_order_id": razorpay_order_id})
        if tx:
            await db.bookings.update_one({"_id": ObjectId(tx["booking_id"])}, {"$set": {"status": "confirmed", "payment_status": "paid"}})
        return {"status": "success", "message": "Payment verified successfully"}
    except razorpay_mod.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    except Exception as e:
        logger.error(f"Payment verification failed: {e}")
        raise HTTPException(status_code=500, detail="Payment verification failed")


@router.get("/payments/razorpay/status/{order_id}")
async def get_razorpay_payment_status(order_id: str):
    if not razorpay_client:
        raise HTTPException(status_code=400, detail="Razorpay not configured")
    try:
        order = razorpay_client.order.fetch(order_id)
        payments = razorpay_client.order.payments(order_id)
        tx = await db.payment_transactions.find_one({"razorpay_order_id": order_id})
        return {"order_id": order_id, "status": order["status"], "amount_paid": order.get("amount_paid", 0) / 100, "payment_status": tx.get("payment_status") if tx else "unknown", "payments": payments.get("items", [])}
    except Exception as e:
        logger.error(f"Failed to fetch payment status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch payment status")


# ---- PayPal ----

@router.post("/payments/paypal/create-order")
async def create_paypal_order(request: PayPalOrderRequest, user: dict = Depends(get_current_user)):
    if not paypal_client:
        raise HTTPException(status_code=400, detail="PayPal not configured")
    booking = await db.bookings.find_one({"_id": ObjectId(request.booking_id)})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    try:
        order_req = OrdersCreateRequest()
        order_req.prefer("return=representation")
        order_req.request_body({"intent": "CAPTURE", "purchase_units": [{"reference_id": request.booking_id, "amount": {"currency_code": "USD", "value": f"{booking['total_price']:.2f}"}}], "application_context": {"return_url": request.return_url, "cancel_url": request.cancel_url}})
        response = paypal_client.execute(order_req)
        await db.payment_transactions.insert_one({"booking_id": request.booking_id, "paypal_order_id": response.result.id, "amount": booking["total_price"], "currency": "USD", "payment_status": "created", "payment_method": "paypal", "created_at": datetime.now(timezone.utc)})
        approval_url = next((link.href for link in response.result.links if link.rel == "approve"), None)
        return {"order_id": response.result.id, "status": response.result.status, "approval_url": approval_url}
    except Exception as e:
        logger.error(f"PayPal order creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Payment order creation failed: {e}")


@router.post("/payments/paypal/capture/{order_id}")
async def capture_paypal_order(order_id: str):
    if not paypal_client:
        raise HTTPException(status_code=400, detail="PayPal not configured")
    try:
        response = paypal_client.execute(OrdersCaptureRequest(order_id))
        await db.payment_transactions.update_one({"paypal_order_id": order_id}, {"$set": {"payment_status": "paid", "captured_at": datetime.now(timezone.utc)}})
        tx = await db.payment_transactions.find_one({"paypal_order_id": order_id})
        if tx:
            await db.bookings.update_one({"_id": ObjectId(tx["booking_id"])}, {"$set": {"status": "confirmed", "payment_status": "paid"}})
        return {"status": "success", "order_id": order_id, "capture_id": response.result.purchase_units[0].payments.captures[0].id}
    except Exception as e:
        logger.error(f"PayPal capture failed: {e}")
        raise HTTPException(status_code=500, detail="Payment capture failed")


# ---- Skrill ----

@router.post("/payments/skrill/prepare")
async def prepare_skrill_payment(request: SkrillPaymentRequest):
    if not SKRILL_MERCHANT_EMAIL or not SKRILL_API_PASSWORD:
        raise HTTPException(status_code=400, detail="Skrill not configured")
    booking = await db.bookings.find_one({"_id": ObjectId(request.booking_id)})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    try:
        payload = {
            "pay_to_email": SKRILL_MERCHANT_EMAIL, "amount": f"{booking['total_price']:.2f}", "currency": "EUR",
            "return_url": request.return_url, "cancel_url": request.cancel_url, "status_url": request.status_url,
            "transaction_id": str(booking["_id"]), "detail1_description": f"Booking: {booking.get('customer_name', '')}",
            "detail1_text": f"Date: {booking.get('date', '')} {booking.get('start_time', '')}",
        }
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post("https://pay.skrill.com", data=payload, timeout=30)
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to create Skrill session")
            session_id = resp.text
            await db.payment_transactions.insert_one({"booking_id": request.booking_id, "skrill_session_id": session_id, "amount": booking["total_price"], "currency": "EUR", "payment_status": "created", "payment_method": "skrill", "created_at": datetime.now(timezone.utc)})
            return {"session_id": session_id, "payment_url": f"https://pay.skrill.com/?sid={session_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Skrill payment preparation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Payment preparation failed: {e}")


@router.post("/payments/skrill/status")
async def skrill_payment_status(request: Request):
    try:
        form_data = await request.form()
        transaction_id = form_data.get("transaction_id")
        status = form_data.get("status")
        mb_transaction_id = form_data.get("mb_transaction_id")

        await db.payment_transactions.update_one(
            {"booking_id": transaction_id},
            {"$set": {"payment_status": "paid" if status == "2" else "failed", "skrill_transaction_id": mb_transaction_id, "updated_at": datetime.now(timezone.utc)}},
        )
        if status == "2":
            booking = await db.bookings.find_one({"_id": ObjectId(transaction_id)})
            if booking:
                await db.bookings.update_one({"_id": ObjectId(transaction_id)}, {"$set": {"status": "confirmed", "payment_status": "paid"}})
        return {"status": "processed"}
    except Exception as e:
        logger.error(f"Skrill webhook processing failed: {e}")
        return {"status": "error"}

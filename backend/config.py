import os
import logging
import razorpay
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment

logger = logging.getLogger(__name__)

# Auth
JWT_ALGORITHM = "HS256"
JWT_SECRET = os.environ["JWT_SECRET"]

# Email
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

# Payment gateways
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET", "")
PAYPAL_MODE = os.environ.get("PAYPAL_MODE", "sandbox")
SKRILL_MERCHANT_EMAIL = os.environ.get("SKRILL_MERCHANT_EMAIL", "")
SKRILL_API_PASSWORD = os.environ.get("SKRILL_API_PASSWORD", "")

# App
APP_DOMAIN = os.environ.get("APP_DOMAIN", "spancle.com")
FRONTEND_URL = os.environ.get("REACT_APP_FRONTEND_URL", f"https://{APP_DOMAIN}")

# Initialize Resend
if RESEND_API_KEY:
    import resend
    resend.api_key = RESEND_API_KEY

# Initialize Razorpay
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
else:
    razorpay_client = None

# Initialize PayPal
if PAYPAL_CLIENT_ID and PAYPAL_SECRET:
    _env = (
        SandboxEnvironment(client_id=PAYPAL_CLIENT_ID, client_secret=PAYPAL_SECRET)
        if PAYPAL_MODE == "sandbox"
        else LiveEnvironment(client_id=PAYPAL_CLIENT_ID, client_secret=PAYPAL_SECRET)
    )
    paypal_client = PayPalHttpClient(_env)
else:
    paypal_client = None

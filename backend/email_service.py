import asyncio
import logging
import resend

from config import RESEND_API_KEY, SENDER_EMAIL

logger = logging.getLogger(__name__)


def build_booking_confirmation_html(booking: dict, venue_name: str, court_name: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Arial', sans-serif; background-color: #f5f5f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #059669 0%, #047857 100%); padding: 40px 20px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 28px; }}
            .content {{ padding: 40px 30px; }}
            .booking-details {{ background-color: #f0fdf4; border-left: 4px solid #059669; padding: 20px; margin: 20px 0; border-radius: 8px; }}
            .detail-row {{ margin: 10px 0; }}
            .label {{ font-weight: bold; color: #1e1b4b; }}
            .value {{ color: #57534e; }}
            .footer {{ background-color: #f5f5f4; padding: 20px; text-align: center; color: #78716c; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h1>Booking Confirmed!</h1></div>
            <div class="content">
                <p>Hi {booking.get('customer_name', 'there')},</p>
                <p>Your booking has been confirmed. Here are your details:</p>
                <div class="booking-details">
                    <div class="detail-row"><span class="label">Venue:</span> <span class="value">{venue_name}</span></div>
                    <div class="detail-row"><span class="label">Court:</span> <span class="value">{court_name}</span></div>
                    <div class="detail-row"><span class="label">Date:</span> <span class="value">{booking.get('date')}</span></div>
                    <div class="detail-row"><span class="label">Time:</span> <span class="value">{booking.get('start_time')} - {booking.get('end_time')}</span></div>
                    <div class="detail-row"><span class="label">Total:</span> <span class="value">${booking.get('total_price', 0):.2f}</span></div>
                </div>
                <p>We look forward to seeing you!</p>
            </div>
            <div class="footer"><p>&copy; 2026 Spancle Sports Venue Management</p></div>
        </div>
    </body>
    </html>
    """


def build_cancellation_html(booking: dict, venue_name: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Arial', sans-serif; background-color: #f5f5f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%); padding: 40px 20px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 28px; }}
            .content {{ padding: 40px 30px; }}
            .footer {{ background-color: #f5f5f4; padding: 20px; text-align: center; color: #78716c; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h1>Booking Cancelled</h1></div>
            <div class="content">
                <p>Hi {booking.get('customer_name', 'there')},</p>
                <p>Your booking at {venue_name} on {booking.get('date')} at {booking.get('start_time')} has been cancelled.</p>
                <p>If you have any questions, please contact the venue directly.</p>
            </div>
            <div class="footer"><p>&copy; 2026 Spancle Sports Venue Management</p></div>
        </div>
    </body>
    </html>
    """


def build_password_reset_html(name: str, reset_link: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Arial', sans-serif; background-color: #f5f5f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #059669 0%, #047857 100%); padding: 40px 20px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 28px; }}
            .content {{ padding: 40px 30px; }}
            .btn {{ display: inline-block; padding: 14px 28px; background-color: #059669; color: white; text-decoration: none; border-radius: 12px; font-weight: bold; }}
            .footer {{ background-color: #f5f5f4; padding: 20px; text-align: center; color: #78716c; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h1>Reset Your Password</h1></div>
            <div class="content">
                <p>Hi {name},</p>
                <p>We received a request to reset your password. Click the button below to set a new password:</p>
                <p style="text-align: center; margin: 30px 0;"><a href="{reset_link}" class="btn">Reset Password</a></p>
                <p style="color: #78716c; font-size: 14px;">This link expires in 1 hour. If you didn't request this, you can safely ignore this email.</p>
            </div>
            <div class="footer"><p>&copy; 2026 Spancle Sports Venue Management</p></div>
        </div>
    </body>
    </html>
    """


async def send_booking_confirmation_email(booking: dict, customer_email: str, venue_name: str, court_name: str):
    if not RESEND_API_KEY or RESEND_API_KEY == "re_demo_key":
        logger.info(f"Email notification skipped (demo mode): Booking confirmation to {customer_email}")
        return
    try:
        params = {"from": SENDER_EMAIL, "to": [customer_email], "subject": f"Booking Confirmed - {venue_name}", "html": build_booking_confirmation_html(booking, venue_name, court_name)}
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Booking confirmation email sent to {customer_email}")
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email: {e}")


async def send_booking_cancellation_email(booking: dict, customer_email: str, venue_name: str):
    if not RESEND_API_KEY or RESEND_API_KEY == "re_demo_key":
        logger.info(f"Email notification skipped (demo mode): Cancellation notice to {customer_email}")
        return
    try:
        params = {"from": SENDER_EMAIL, "to": [customer_email], "subject": f"Booking Cancelled - {venue_name}", "html": build_cancellation_html(booking, venue_name)}
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Cancellation email sent to {customer_email}")
    except Exception as e:
        logger.error(f"Failed to send cancellation email: {e}")


async def send_password_reset_email(email: str, name: str, reset_link: str):
    if not RESEND_API_KEY or RESEND_API_KEY == "re_demo_key":
        logger.info(f"Password reset link (demo mode): {reset_link}")
        return
    try:
        params = {"from": SENDER_EMAIL, "to": [email], "subject": "Password Reset - Spancle", "html": build_password_reset_html(name, reset_link)}
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Password reset email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")

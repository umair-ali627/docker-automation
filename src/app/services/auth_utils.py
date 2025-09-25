import secrets
import redis.asyncio as redis
from datetime import timedelta
from decouple import config
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)
redis_client = redis.from_url(config("REDIS_URL"), decode_responses=True)

async def generate_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)

async def store_otp(key: str, otp: str, ttl: timedelta = timedelta(minutes=5)):
    await redis_client.setex(key, int(ttl.total_seconds()), otp)

async def verify_and_delete_otp(key: str, provided_otp: str) -> bool:
    stored_otp = await redis_client.get(key)
    if stored_otp and stored_otp == provided_otp:
        await redis_client.delete(key)
        return True
    return False

# async def send_otp_email(to_email: str, otp: str, subject: str = "Your ConvoiAI OTP for Email Verification") -> bool:
#     message = Mail(
#         from_email=config('SENDGRID_FROM_EMAIL'),
#         to_emails=to_email,
#         subject=subject,
#         plain_text_content=f"Your OTP is: {otp}. It expires in 5 minutes. For ConvoiAI.")
#     try:
#         sg = SendGridAPIClient(config('SENDGRID_API_KEY'))
#         response = sg.send(message)
#         if response.status_code != 202:
#             logger.error(f"Failed to send OTP email to {to_email}: Status {response.status_code}, Body: {response.body}")
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send OTP email")
#         logger.info(f"OTP email sent to {to_email}")
#         return True
#     except Exception as e:
#         logger.error(f"Email error for {to_email}: {str(e)}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send OTP email: {str(e)}")

async def send_otp_email(
    to_email: str, 
    otp: str, 
    subject: str = "Your ConvoiAI OTP for Email Verification"
) -> bool:
    """
    Sends a One-Time Password (OTP) email using SendGrid with both HTML and plain-text fallback.
    """

    plain_text_content = f"""\
Hello,

Thank you for registering with ConvoiAI.

Please use the following One-Time Password (OTP) to verify your email address:

{otp}

This code will expire in 5 minutes.

If you did not request this verification, please ignore this email.

Best regards,  
The ConvoiAI Team
"""

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color:#f9f9f9; padding:20px; color:#333;">
        <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px; background:white; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1); padding:30px;">
          <tr>
            <td style="text-align:center;">
              <h2 style="color:#FF5C00;">ConvoiAI Email Verification</h2>
            </td>
          </tr>
          <tr>
            <td style="font-size:15px; line-height:1.6; color:#444;">
              <p>Hello,</p>
              <p>Thank you for registering with <strong>ConvoiAI</strong>.</p>
              <p>Please use the following One-Time Password (OTP) to verify your email address:</p>
              <p style="text-align:center; margin:30px 0;">
                <span style="font-size:26px; font-weight:bold; color:#FF5C00; letter-spacing:4px;">{otp}</span>
              </p>
              <p>This code will expire in <strong>5 minutes</strong>.</p>
              <p>If you did not request this verification, please ignore this email.</p>
              <br>
              <p>Best regards, <br><strong>The ConvoiAI Team</strong></p>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    message = Mail(
        from_email=config("SENDGRID_FROM_EMAIL"),
        to_emails=to_email,
        subject=subject,
        plain_text_content=plain_text_content,
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(config("SENDGRID_API_KEY"))
        response = sg.send(message)

        if response.status_code == 429:
            logger.error(f"SendGrid rate limit exceeded for {to_email}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Email sending rate limit exceeded. Try again later."
            )

        if response.status_code != 202:
            logger.error(
                f"Failed to send OTP email to {to_email}: "
                f"Status {response.status_code}, Body: {response.body}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP email"
            )

        logger.info(f"OTP email sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Email error for {to_email}: {str(e)}")
        if "429" in str(e):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Email sending rate limit exceeded. Try again later."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP email: {str(e)}"
        )
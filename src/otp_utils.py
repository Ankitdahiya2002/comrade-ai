# src/otp_utils.py
import streamlit as st
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

class OTPManager:
    """
    Manages real-time OTP delivery and verification via Twilio Verify API.
    Ensure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_VERIFY_SID
    are present in .streamlit/secrets.toml.
    """
    def __init__(self):
        try:
            self.account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
            self.auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
            self.verify_sid = st.secrets["TWILIO_VERIFY_SID"]
            self.client = Client(self.account_sid, self.auth_token)
        except KeyError as e:
            st.error(f"Missing Twilio Secret: {e}")
            self.client = None

    def send_code(self, phone: str):
        """Triggers an SMS verification code to the given phone number."""
        if not self.client:
            return False, "Twilio client not initialized."
        try:
            # Ensure phone starts with '+'
            if not phone.startswith("+"):
                phone = f"+91{phone}" # Default to India if no prefix
            
            self.client.verify.v2.services(self.verify_sid) \
                .verifications \
                .create(to=phone, channel='sms')
            return True, "OTP sent successfully!"
        except TwilioRestException as e:
            return False, f"Twilio Error: {e.msg}"
        except Exception as e:
            return False, f"Unexpected Error: {str(e)}"

    def check_code(self, phone: str, code: str):
        """Verifies if the entered code is correct for the phone number."""
        if not self.client:
            return False
        try:
            if not phone.startswith("+"):
                phone = f"+91{phone}"
            
            result = self.client.verify.v2.services(self.verify_sid) \
                .verification_checks \
                .create(to=phone, code=code)
            return result.status == "approved"
        except TwilioRestException:
            return False
        except Exception:
            return False

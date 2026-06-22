from abc import ABC, abstractmethod


class SMSService(ABC):
    @abstractmethod
    async def send_otp(self, phone_number: str, otp_code: str) -> bool:
        raise NotImplementedError


class ConsoleSMSService(SMSService):
    async def send_otp(self, phone_number: str, otp_code: str) -> bool:
        print(f"[DEV OTP] Phone: {phone_number} | OTP: {otp_code}")
        return True


class MSG91SMSService(SMSService):
    # Reads MSG91_API_KEY, MSG91_SENDER_ID, MSG91_DLT_TEMPLATE_ID from .env
    # Implement when DLT registration is complete
    async def send_otp(self, phone_number: str, otp_code: str) -> bool:
        raise NotImplementedError("MSG91 integration not yet implemented")

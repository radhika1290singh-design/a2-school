import uuid
from pydantic import BaseModel, ConfigDict

from app.models.otp_request import OtpPurpose


class SendOtpRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    subdomain: str
    phone_number: str
    purpose: OtpPurpose


class ActivateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    subdomain: str
    phone_number: str
    otp_code: str
    new_password: str


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    subdomain: str
    phone_number: str
    password: str


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    subdomain: str
    phone_number: str
    otp_code: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    current_password: str
    new_password: str


class SuperAdminLoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    phone_number: str
    password: str


class MessageResponse(BaseModel):
    message: str


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str
    role: str
    school_id: uuid.UUID | None = None
    subdomain: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class MeResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    phone_number: str
    role: str
    status: str
    school_id: uuid.UUID | None = None
    subdomain: str | None = None
    school_name: str | None = None
    school_logo_url: str | None = None
    school_primary_color: str | None = None
    school_secondary_color: str | None = None

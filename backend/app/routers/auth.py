import random
import string
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.otp_request import OtpPurpose, OtpRequest
from app.models.school import School, SchoolStatus
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import (
    ActivateRequest,
    ChangePasswordRequest,
    LoginRequest,
    MeResponse,
    MessageResponse,
    ResetPasswordRequest,
    SendOtpRequest,
    SuperAdminLoginRequest,
    TokenResponse,
    UserInfo,
)
from app.services.sms import SMSService
from app.dependencies.auth import get_sms_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _get_active_school(subdomain: str, db: AsyncSession) -> School:
    result = await db.execute(select(School).where(School.subdomain == subdomain))
    school = result.scalar_one_or_none()
    if not school or school.status != SchoolStatus.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
    return school


async def _get_user_by_phone(school_id: uuid.UUID, phone_number: str, db: AsyncSession) -> User:
    result = await db.execute(
        select(User).where(User.school_id == school_id, User.phone_number == phone_number)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


async def _generate_and_store_otp(
    school_id: uuid.UUID,
    phone_number: str,
    purpose: OtpPurpose,
    db: AsyncSession,
) -> str:
    # Invalidate all prior unused OTPs for same (school_id, phone_number, purpose)
    await db.execute(
        update(OtpRequest)
        .where(
            OtpRequest.school_id == school_id,
            OtpRequest.phone_number == phone_number,
            OtpRequest.purpose == purpose,
            OtpRequest.used == False,  # noqa: E712
        )
        .values(used=True)
    )

    otp_code = _generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    otp_record = OtpRequest(
        school_id=school_id,
        phone_number=phone_number,
        code_hash=hash_password(otp_code),
        purpose=purpose,
        expires_at=expires_at,
    )
    db.add(otp_record)
    await db.flush()
    return otp_code


async def _verify_otp(
    school_id: uuid.UUID,
    phone_number: str,
    purpose: OtpPurpose,
    otp_code: str,
    db: AsyncSession,
) -> OtpRequest:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(OtpRequest)
        .where(
            OtpRequest.school_id == school_id,
            OtpRequest.phone_number == phone_number,
            OtpRequest.purpose == purpose,
            OtpRequest.used == False,  # noqa: E712
            OtpRequest.expires_at > now,
        )
        .order_by(OtpRequest.created_at.desc())
        .limit(1)
    )
    otp_record = result.scalar_one_or_none()
    if not otp_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired or not found")

    if not verify_password(otp_code, otp_record.code_hash):
        otp_record.attempt_count += 1
        if otp_record.attempt_count >= 3:
            otp_record.used = True
        await db.flush()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    return otp_record


def _build_token_response(user: User, subdomain: str | None) -> TokenResponse:
    token = create_access_token(
        user_id=user.id,
        school_id=user.school_id,
        role=user.role.value,
        subdomain=subdomain,
    )
    return TokenResponse(
        access_token=token,
        user=UserInfo(
            id=user.id,
            full_name=user.full_name,
            role=user.role.value,
            school_id=user.school_id,
            subdomain=subdomain,
        ),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/send-otp", response_model=MessageResponse)
async def send_otp(
    body: SendOtpRequest,
    db: AsyncSession = Depends(get_db),
    sms: SMSService = Depends(get_sms_service),
) -> MessageResponse:
    school = await _get_active_school(body.subdomain, db)
    user = await _get_user_by_phone(school.id, body.phone_number, db)

    if body.purpose == OtpPurpose.activation and user.status != UserStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is already active")
    if body.purpose == OtpPurpose.password_reset and user.status != UserStatus.active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is not yet active")

    otp_code = await _generate_and_store_otp(school.id, body.phone_number, body.purpose, db)
    await db.commit()

    sent = await sms.send_otp(body.phone_number, otp_code)
    if not sent:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send OTP")

    return MessageResponse(message="OTP sent successfully")


@router.post("/activate", response_model=TokenResponse)
async def activate(
    body: ActivateRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    school = await _get_active_school(body.subdomain, db)
    user = await _get_user_by_phone(school.id, body.phone_number, db)

    if user.status != UserStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is already active")

    try:
        validate_password_strength(body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    otp_record = await _verify_otp(school.id, body.phone_number, OtpPurpose.activation, body.otp_code, db)

    user.password_hash = hash_password(body.new_password)
    user.status = UserStatus.active
    otp_record.used = True
    await db.commit()

    return _build_token_response(user, school.subdomain)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    school = await _get_active_school(body.subdomain, db)
    user = await _get_user_by_phone(school.id, body.phone_number, db)

    if user.status == UserStatus.pending:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not yet activated")

    if not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return _build_token_response(user, school.subdomain)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    school = await _get_active_school(body.subdomain, db)
    user = await _get_user_by_phone(school.id, body.phone_number, db)

    if user.status != UserStatus.active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is not active")

    try:
        validate_password_strength(body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    otp_record = await _verify_otp(school.id, body.phone_number, OtpPurpose.password_reset, body.otp_code, db)

    user.password_hash = hash_password(body.new_password)
    otp_record.used = True
    await db.commit()

    return MessageResponse(message="Password reset successfully. Please log in.")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    if not current_user.password_hash or not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    try:
        validate_password_strength(body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    current_user.password_hash = hash_password(body.new_password)
    await db.commit()

    return MessageResponse(message="Password changed successfully")


@router.get("/me", response_model=MeResponse)
async def me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    school = None
    if current_user.school_id:
        school = await db.get(School, current_user.school_id)

    return MeResponse(
        id=current_user.id,
        full_name=current_user.full_name,
        phone_number=current_user.phone_number,
        role=current_user.role.value,
        status=current_user.status.value,
        school_id=current_user.school_id,
        subdomain=school.subdomain if school else None,
        school_name=school.name if school else None,
        school_logo_url=school.logo_url if school else None,
        school_primary_color=school.primary_color if school else None,
        school_secondary_color=school.secondary_color if school else None,
    )


@router.post("/super-admin/login", response_model=TokenResponse)
async def super_admin_login(
    body: SuperAdminLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    result = await db.execute(
        select(User).where(
            User.phone_number == body.phone_number,
            User.role == UserRole.super_admin,
        )
    )
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return _build_token_response(user, subdomain=None)

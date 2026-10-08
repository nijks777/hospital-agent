import uuid
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2)]


class RegisterHospitalRequest(BaseModel):
    hospital_name: Annotated[Text, StringConstraints(max_length=200)]
    city: Annotated[Text, StringConstraints(max_length=100)]
    contact_name: Annotated[Text, StringConstraints(max_length=120)]
    email: EmailStr
    # Digits, spaces, +, - and brackets; 7–20 characters (e.g. "+91 98765 43210").
    phone: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\+?[0-9 ()-]{7,20}$")]
    password: str = Field(min_length=8, max_length=128)


class RegisterHospitalResponse(BaseModel):
    hospital_id: uuid.UUID
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{6}$")]


class ResendCodeRequest(BaseModel):
    email: EmailStr

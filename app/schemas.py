from pydantic import BaseModel
from typing import Optional
from pydantic import BaseModel, EmailStr


class DoctorImageValidationResponse(BaseModel):
    id: Optional[int] = None  # Make the id field optional
    image_path: str
    doctor_name: Optional[str] = None
    rating: Optional[int] = None
    comments: Optional[str] = None
    disease_name: Optional[str] = None
    category: Optional[str] = None

class DoctorImageValidationRequest(BaseModel):
    doctor_name: str
    rating: int
    comments: Optional[str] = None
    disease_name: str
    category: str


class DoctorSchema(BaseModel):
    doctor_name: str
    hospital: Optional[str]
    hospital_address: Optional[str]
    contact_number: Optional[str]
    email: Optional[str]  # Use EmailStr for email validation
    specialization: Optional[str]
    registration_id: str


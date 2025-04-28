from typing import Optional
from pydantic import BaseModel, EmailStr

class DoctorImageValidationResponse(BaseModel):
    id: Optional[int] = None
    image_path: str
    mask_path: Optional[str] = None
    doctor_name: Optional[str] = None
    rating: Optional[int] = None
    comments: Optional[str] = None
    mask_comments: Optional[str] = None
    disease_name: Optional[str] = None
    category: Optional[str] = None
    
    class Config:
        orm_mode = True

class DoctorImageValidationRequest(BaseModel):
    doctor_name: str
    rating: int
    comments: Optional[str] = None
    disease_name: str
    category: str


class DoctorSchema(BaseModel):
    doctor_name: str
    hospital: Optional[str] = None
    hospital_address: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None  # Use EmailStr for email validation
    specialization: Optional[str] = None
    registration_id: str




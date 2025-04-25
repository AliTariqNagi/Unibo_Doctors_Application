# from pydantic import BaseModel
# from typing import Optional
# from fastapi import UploadFile

# class DoctorImageValidationRequest(BaseModel):
#     doctor_name: str
#     rating: int
#     comments: Optional[str] = None
#     disease_name: str
#     file: UploadFile  # Change image_path to file of type UploadFile

# class DoctorImageValidationResponse(BaseModel):
#     id: int  # Add this line
#     doctor_name: str
#     rating: int
#     comments: Optional[str] = None
#     disease_name: str
#     image_path: str

#     class Config:
#         orm_mode = True


# from pydantic import BaseModel
# from typing import Optional
# from fastapi import UploadFile

# class DoctorImageValidationRequest(BaseModel):
#     doctor_name: str
#     rating: int
#     comments: Optional[str] = None
#     disease_name: str
#     category: str  # Add category field

# class DoctorImageValidationResponse(BaseModel):
#     id: int
#     image_path: str

#     class Config:
#         orm_mode = True


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


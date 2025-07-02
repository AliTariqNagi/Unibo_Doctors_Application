# schemas.py
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime  # Import datetime
from enum import Enum


class CropQualityRatingEnum(int, Enum):
    very_poor = 1  # Very poor quality
    poor = 2       # Poor quality
    fair = 3       # Fair quality
    acceptable = 4 # Acceptable/neutral quality
    good = 5       # Good quality
    very_good = 6  # Very good quality
    excellent = 7  # Excellent quality

class CropDiagnosisEnum(str, Enum):
    # These values must exactly match the 'value' attributes in your HTML <option> tags
    iatrogenic_drug_induced_exanthema = "iatrogenic_drug_induced_exanthema"
    maculopapular_exanthema = "maculopapular_exanthema"
    morbilliform_exanthema = "morbilliform_exanthema"
    polymorphous_exanthema = "polymorphous_exanthema"
    viral_exanthema = "viral_exanthema"
    urticaria = "urticaria"
    pediculosis = "pediculosis"
    scabies = "scabies"
    chickenpox = "chickenpox"


class DoctorImageValidationResponse(BaseModel):
    id: Optional[int] = None
    image_path: Optional[str]
    mask_path: Optional[str] = None
    crop_path: Optional[str] = None               # NEW
    crop_mask_path: Optional[str] = None          # NEW
    doctor_name: Optional[str] = None
    #rating: Optional[int] = None
    comments: Optional[str] = None
    mask_comments: Optional[str] = None
    disease_name: Optional[str]
    category: Optional[str] = None
    created_at: Optional[datetime] = None
    #years_of_experience: Optional[int] = None
    real_generated: Optional[str] = None
    realism_rating: Optional[int] = None
    image_precision: Optional[str] = None
    skin_color_precision: Optional[int] = None
    confidence_level: Optional[int] = None
    crop_quality_rating: Optional[int] = None
    crop_diagnosis: Optional[str] = None
    fitzpatrick_scale: Optional[str] = None

    class Config:
        orm_mode = True


# class DoctorImageValidationRequest(BaseModel):
#     doctor_name: str
#     rating: int
#     comments: Optional[str] = None
#     mask_comments: Optional[str] = None
#     disease_name: str
#     category: str
#     #years_of_experience: Optional[int] = None  
#     real_generated: str
#     realism_rating: Optional[int] = None
#     image_precision: str
#     skin_color_precision: Optional[int] = None
#     confidence_level: Optional[int] = None
#     crop_quality_rating: Optional[int] = None
#     crop_diagnosis: str
#     fitzpatrick_scale: Optional[str] = None

class DoctorImageValidationRequest(BaseModel):
    # These fields are now required when creating a new entry
    image_path: str                 # <--- ADDED/CHANGED
    mask_path: Optional[str] = None # <--- ADDED/CHANGED
    crop_path: Optional[str] = None # <--- ADDED/CHANGED
    crop_mask_path: Optional[str] = None # <--- ADDED/CHANGED

    doctor_name: str
    #rating: int
    comments: Optional[str] = None
    mask_comments: Optional[str] = None
    disease_name: str
    category: str
    real_generated: str
    realism_rating: Optional[int] = None
    image_precision: str
    skin_color_precision: Optional[int] = None
    confidence_level: Optional[int] = None
    crop_quality_rating: Optional[int] = None
    crop_diagnosis: str
    fitzpatrick_scale: Optional[str] = None

    class Config:
        orm_mode = True



class DoctorSchema(BaseModel):
    doctor_name: str
    hospital: Optional[str] = None
    hospital_address: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    specialization: Optional[str] = None
    registration_id: str
    years_of_experience: Optional[int] = None

    class Config:
        orm_mode = True



class SkinDiseaseImageResponse(BaseModel):
    id: Optional[int] = None
    disease_name_amended: Optional[str] = None
    disease_name: Optional[str] = None
    persona_digits: Optional[str] = None
    example_digit: Optional[str] = None
    image_name: str
    mask_name: Optional[str] = None
    image_path: str
    mask_path: Optional[str] = None
    doctor_name: Optional[str] = None
    rating: Optional[int] = None
    comments: Optional[str] = None
    category: Optional[str] = None
    years_of_experience: Optional[int] = None
    real_generated: Optional[str] = None
    realism_rating: Optional[int] = None
    image_precision: Optional[str] = None
    skin_color_precision: Optional[int] = None
    confidence_level: Optional[int] = None
    crop_quality_rating: Optional[int] = None
    crop_diagnosis: Optional[str] = None
    fitzpatrick_scale: Optional[str] = None
    created_at: Optional[datetime] = None
    crop_image_name: Optional[str] = None
    crop_image_path: Optional[str] = None
    crop_mask_name: Optional[str] = None
    crop_mask_path: Optional[str] = None


    class Config:
        orm_mode = True


class SkinDiseaseImageModel(BaseModel):
    id: int
    disease_name_amended: str | None = None
    disease_name: str | None = None
    persona_digits: str | None = None
    example_digit: str | None = None
    image_name: str
    mask_name: str | None = None
    image_path: str
    mask_path: str | None = None
    doctor_name: str | None = None
    rating: int | None = None
    comments: str | None = None
    category: str | None = None
    years_of_experience: int | None = None
    real_generated: str | None = None
    realism_rating: int | None = None
    image_precision: str | None = None
    skin_color_precision: int | None = None
    confidence_level: int | None = None
    crop_quality_rating: int | None = None
    crop_diagnosis: str | None = None
    fitzpatrick_scale: str | None = None
    created_at: datetime | None = None
    crop_image_name: Optional[str] = None
    crop_image_path: Optional[str] = None
    crop_mask_name: Optional[str] = None
    crop_mask_path: Optional[str] = None


    class Config:
        from_attributes = True

class SkinDiseaseImageResponse2(BaseModel):
    data: List[SkinDiseaseImageModel]


class DoctorImageValidationUpdateRequest(BaseModel):
    doctor_name: Optional[str] = None
    rating: Optional[int] = None
    comments: Optional[str] = None
    disease_name: Optional[str] = None
    category: Optional[str] = None
    years_of_experience: Optional[int] = None
    real_generated: Optional[str] = None
    realism_rating: Optional[int] = None
    image_precision: Optional[str] = None
    skin_color_precision: Optional[int] = None
    confidence_level: Optional[int] = None
    crop_quality_rating: Optional[int] = None
    crop_diagnosis: Optional[str] = None
    fitzpatrick_scale: Optional[str] = None

    class Config:
        orm_mode = True


# NEW: Pydantic models for the new Crop Image Validation flow
class CropImageValidationRequest(BaseModel):
    image_filename: str # This will be the original filename (e.g., "crop1.jpg")
    doctor_name: str
    comments: Optional[str] = None
    # Using the Enum for validation and consistency
    crop_diagnosis: CropDiagnosisEnum
    fitzpatrick_scale: str # Assuming Fitzpatrick is a string 'I', 'II', etc.


class CropImageValidationResponse(BaseModel): # No longer inherits from CropImageValidationRequest
    id: int
    image_filename: str # Added this field to match frontend/FastAPI expectation
    image_path: str     # Keep this if needed in response
    doctor_name: str
    comments: Optional[str] = None
    crop_diagnosis: CropDiagnosisEnum
    fitzpatrick_scale: str
    created_at: datetime

    class Config:
        orm_mode = True


class CropImageFilenameResponse(BaseModel):
    image_filename: str # This is the field the frontend expects and was missing!

    class Config:
        orm_mode = True # Enable ORM mode for easier conversion from SQLAlchemy objects


# schemas.py
from pydantic import BaseModel, Field # <--- Add Field here
from typing import Optional, List
from datetime import datetime

# Schema for requesting rating data for a single image
class SingleCropImageRatingRequest(BaseModel):
    image_path: str
    doctor_name: str
    comments: Optional[str] = None
    crop_quality_rating: Optional[int] = Field(None, ge=1, le=7)
    crop_diagnosis: Optional[str] = None

# Schema for the response after rating images
class CropImageRatingResponse(BaseModel):
    id: int
    image_path: str
    doctor_name: str
    comments: Optional[str] = None
    crop_quality_rating: Optional[int] = None
    crop_diagnosis: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

# Schema for receiving a batch of rating data from the frontend
class BatchCropImageRatingRequest(BaseModel):
    validations: List[SingleCropImageRatingRequest] # Renamed from 'validations' to 'ratings' for clarity if you prefer, but 'validations' is fine if it aligns with your API

# Schema for serving image metadata to the frontend
class CropImageMetadata(BaseModel):
    image_path: str


# Schema for the request body when submitting a single crop quality rating
class SingleCropQualityRatingRequest(BaseModel):
    image_path: str # The URL path of the image being rated (e.g., /images/crop_quality_rating_images/image.jpg)
    doctor_name: str
    comments: Optional[str] = None
    crop_quality_rating: int = Field(..., ge=1, le=7) # Rating from 1 to 7, required

# Schema for the response after a single image rating submission
class SingleCropQualityRatingResponse(BaseModel):
    message: str
    # You could add more fields here if the backend returns them, e.g.:
    # id: int
    # image_path: str

# Schema for serving metadata of a single image to the frontend
class SingleCropImageMetadata(BaseModel):
    image_path: str # The URL path of the image to display

# --- NEW SCHEMA: For Skin Tone Classification Request ---
class SkinToneClassificationRequest(BaseModel):
    doctor_name: str # Added doctor_name
    fitzpatrick_scale: str
    # These fields are now part of SkinToneClassification model,
    # but the frontend doesn't send them directly in this request.
    # The backend will fetch and populate them.
    image_name: Optional[str] = None
    image_path: Optional[str] = None
    mask_name: Optional[str] = None
    mask_path: Optional[str] = None
    crop_image_name: Optional[str] = None
    crop_image_path: Optional[str] = None
    crop_mask_name: Optional[str] = None
    crop_mask_path: Optional[str] = None


# --- NEW SCHEMA: For Skin Tone Classification Response ---
class SkinToneClassificationResponse(BaseModel):
    message: str

# --- NEW SCHEMA: For Patient Image Metadata (from /patient_images/{persona_digits}) ---
class PatientImageMetadata(BaseModel):
    image_path: str
    image_name: str
    mask_path: Optional[str] = None
    mask_name: Optional[str] = None



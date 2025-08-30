from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime 
from enum import Enum


class CropQualityRatingEnum(int, Enum):
    very_poor = 1 
    poor = 2     
    fair = 3      
    acceptable = 4 
    good = 5      
    very_good = 6  
    excellent = 7  

class CropDiagnosisEnum(str, Enum):
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
    mask_rating: Optional[int] = None
    comments: Optional[str] = None
    mask_comments: Optional[str] = None
    disease_name: Optional[str]
    category: Optional[str] = None
    created_at: Optional[datetime] = None
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

    #image_path: str                
    #mask_path: Optional[str] = None 
    crop_path: Optional[str] = None # 
    crop_mask_path: Optional[str] = None # 
    mask_rating: Optional[int] = None   #--------------DONE
    doctor_name: str   #--------------DONE
    #rating: int
    comments: Optional[str] = None   #--------------DONE
    mask_comments: Optional[str] = None   #--------------DONE
    #disease_name: str
    #category: str
    real_generated: Optional[str]   #--------------DONE
    realism_rating: Optional[int] = None   #--------------DONE
    image_precision: str   #--------------DONE
    #skin_color_precision: Optional[int] = None
    confidence_level: Optional[int] = None   #--------------DONE
    #crop_quality_rating: Optional[int] = None
    #crop_diagnosis: str
    #fitzpatrick_scale: Optional[str] = None

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



class CropImageValidationRequest(BaseModel):
    image_filename: str # This will be the original filename (e.g., "crop1.jpg")
    doctor_name: str
    comments: Optional[str] = None
    # Using the Enum for validation and consistency
    crop_diagnosis: CropDiagnosisEnum
    fitzpatrick_scale: int
    confidence: int
    #fitzpatrick_scale: str # Assuming Fitzpatrick is a string 'I', 'II', etc.
    #image_filename : str


class CropImageValidationResponse(BaseModel): 
    id: int
    image_filename: str 
    image_path: str    
    doctor_name: str
    comments: Optional[str] = None
    crop_diagnosis: CropDiagnosisEnum
    fitzpatrick_scale: Optional[str]
    #fitzpatrick_scale_score: int
    confidence: int
    created_at: datetime

    class Config:
        orm_mode = True


class CropImageFilenameResponse(BaseModel):
    image_filename: str 

    class Config:
        orm_mode = True 



from pydantic import BaseModel, Field # <--- Add Field here
from typing import Optional, List
from datetime import datetime


class SingleCropImageRatingRequest(BaseModel):
    image_path: str
    doctor_name: str
    comments: Optional[str] = None
    #crop_quality_rating: Optional[int] = Field(None, ge=1, le=7)
    confidence: Optional[int]
    crop_diagnosis: Optional[str] = None


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


class BatchCropImageRatingRequest(BaseModel):
    validations: List[SingleCropImageRatingRequest]


class CropImageMetadata(BaseModel):
    image_path: str



class SingleCropQualityRatingRequest(BaseModel):
    image_path: str 
    doctor_name: str
    comments: Optional[str] = None
    crop_quality_rating: int = Field(..., ge=1, le=7)


class SingleCropQualityRatingResponse(BaseModel):
    message: str



class SingleCropImageMetadata(BaseModel):
    image_path: str 


class SkinToneClassificationRequest(BaseModel):
    doctor_name: str 
    fitzpatrick_scale: str
    confidence: int

    image_name: Optional[str] = None
    image_path: Optional[str] = None
    mask_name: Optional[str] = None
    mask_path: Optional[str] = None
    crop_image_name: Optional[str] = None
    crop_image_path: Optional[str] = None
    crop_mask_name: Optional[str] = None
    crop_mask_path: Optional[str] = None



class SkinToneClassificationResponse(BaseModel):
    message: str


class PatientImageMetadata(BaseModel):
    image_path: str
    image_name: str
    mask_path: Optional[str] = None
    mask_name: Optional[str] = None



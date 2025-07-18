# models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import EmailStr
import os
from datetime import datetime # Import datetime 
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime


DATABASE_URL = "postgresql://admin:admin@localhost/doctor_image_validation"
#DATABASE_URL = os.getenv("DATABASE_URL")


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Define the Doctor model (SQLAlchemy model)
class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    doctor_name = Column(String, nullable=False)
    hospital = Column(String)
    hospital_address = Column(String)
    contact_number = Column(String)
    email = Column(String)
    specialization = Column(String)
    registration_id = Column(String, nullable=False, unique=True)
    years_of_experience = Column(Integer)

class DoctorImageValidation(Base):
    __tablename__ = "doctor_image_validation"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String)   #--------------DONE
    mask_path = Column(String)   #--------------DONE
    crop_path = Column(String)         #--------------DONE      # New
    crop_mask_path = Column(String)      #--------------DONE    # New
    mask_rating = Column(Integer)   #--------------DONE
    doctor_name = Column(String)   #--------------DONE
    comments = Column(String)   #--------------DONE
    mask_comments = Column(String)   #--------------DONE
    disease_name = Column(String)   #--------------DONE
    category = Column(String)   #--------------DONE
    created_at = Column(DateTime, server_default=func.now())   #--------------DONE
    real_generated = Column(String)   #--------------DONE
    realism_rating = Column(Integer)   #--------------DONE
    image_precision = Column(String)   #--------------DONE
    skin_color_precision = Column(Integer)   #--------------DONE
    confidence_level = Column(Integer)   #--------------DONE
    crop_quality_rating = Column(Integer)   #--------------DONE
    crop_diagnosis = Column(String)   #--------------DONE
    fitzpatrick_scale = Column(String)   #--------------DONE


class SkinDiseaseImage(Base):
    __tablename__ = "skin_disease_image"

    id = Column(Integer, primary_key=True, index=True)
    disease_name_amended = Column(String, index=True)
    disease_name = Column(String, index=True)
    persona_digits = Column(String, index=True)
    example_digit = Column(String, index=True)
    image_name = Column(String, nullable=False)
    mask_name = Column(String)  # Can be NULL if no mask
    image_path = Column(String, nullable=False)
    mask_path = Column(String)


    # Crop image info
    crop_image_name = Column(String)
    crop_image_path = Column(String)
    crop_mask_name = Column(String)
    crop_mask_path = Column(String)


    # Add other relevant columns for viewing/editing
    doctor_name = Column(String)
    rating = Column(Integer)
    comments = Column(String)
    category = Column(String)
    years_of_experience = Column(Integer)
    real_generated = Column(String)
    realism_rating = Column(Integer)
    image_precision = Column(String)
    skin_color_precision = Column(Integer)
    confidence_level = Column(Integer)
    crop_quality_rating = Column(Integer)
    crop_diagnosis = Column(String)
    fitzpatrick_scale = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class CropImageValidation(Base):
    __tablename__ = "crop_image_validation" # New table name

    id = Column(Integer, primary_key=True, index=True)
    image_filename = Column(String)
    image_path = Column(String) # Path to the categorized crop image
    doctor_name = Column(String)
    comments = Column(String)
    crop_diagnosis = Column(String)
    fitzpatrick_scale = Column(String)
    created_at = Column(DateTime, server_default=func.now())



class CropImageRating(Base): # Class name remains CropImageRating
    __tablename__ = "crop_image_rating" # <--- CHANGED THIS LINE

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, unique=True, index=True)
    doctor_name = Column(String)
    comments = Column(String)
    crop_quality_rating = Column(Integer)
    crop_diagnosis = Column(String)
    created_at = Column(DateTime, server_default=func.now())


class CropImageQualityRating(Base): # Class name remains CropImageRating
    __tablename__ = "crop_image_quality_rating" # <--- CHANGED THIS LINE

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, unique=True, index=True)
    doctor_name = Column(String)
    comments = Column(String)
    crop_quality_rating = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())


# Create the database tables
Base.metadata.create_all(bind=engine)

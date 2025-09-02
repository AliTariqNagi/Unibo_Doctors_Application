import os
import re
import shutil
import pandas as pd
import logging
import random
from http import HTTPStatus
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from starlette.responses import RedirectResponse
from typing import List, Tuple, Optional, List


from fastapi import UploadFile, File, FastAPI, HTTPException, Depends, Form, Query, status, APIRouter
from fastapi.staticfiles import StaticFiles

from fastapi.responses import JSONResponse, FileResponse

from sqlalchemy.orm import Session
from sqlalchemy import text, text
from sqlalchemy.exc import OperationalError, IntegrityError
from app.models import DoctorImageValidation, SessionLocal, engine, Base, Doctor, SkinDiseaseImage, SessionLocal, CropImageValidation ,CropImageRating, \
    CropImageQualityRating, DoctorImageValidation

from app.schemas import DoctorImageValidationResponse, DoctorSchema, CropImageValidationResponse, CropImageValidationRequest, \
    DoctorImageValidationUpdateRequest, SkinDiseaseImageResponse, SkinDiseaseImageModel, SkinDiseaseImageResponse, PatientImageMetadata, \
    SkinToneClassificationResponse, SkinToneClassificationRequest, BatchCropImageRatingRequest, CropImageMetadata, SkinToneClassificationRequest, \
        SkinToneClassificationResponse, DoctorImageValidationRequest, DoctorImageValidationResponse, CropImageValidationResponse, CropImageValidationRequest, \
            CropImageValidationResponse

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()


app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/frontend", StaticFiles(directory="/root/Unibo_Doctor_App/Unibo_Doctors_Application-main (1) (2)/Unibo_Doctors_Application-main/frontend"), name="static_frontend")

@app.get("/")
async def root():
    return RedirectResponse(url="/frontend/main.html")


######### ----------------------- Serve skin disease images from the external hard drive ---------------------------#################
skin_disease_data_path = "/root/test_data" #"/media/verbose193/E0909AEF909ACB82/Thesis Working Directory/Skin disesases data"
app.mount("/skin_disease_data", StaticFiles(directory=skin_disease_data_path), name="skin_disease_data")

skin_disease_crop_data_path = "/root/test_data" #"/media/verbose193/E0909AEF909ACB82/Thesis Working Directory/Skin disesases data"
app.mount("/skin_disease_data2", StaticFiles(directory=skin_disease_crop_data_path), name="skin_disease_data2")


def find_image_pair(directory="images") -> List[Tuple[str, str]]:
    
    image_pairs = []
    try:
        for filename in os.listdir(directory):
            if "_mask" not in filename:  
                name, ext = os.path.splitext(filename)
                mask_filename = f"{name}_mask{ext}"
                mask_path = os.path.join(directory, mask_filename)
                if os.path.exists(mask_path):
                    image_pairs.append((filename, mask_filename))
        return image_pairs
    except FileNotFoundError:
        print(f"Error: Directory '{directory}' not found.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

@app.get("/categorize_image/", response_model=Optional[DoctorImageValidationResponse])
async def get_first_uncategorized_image():
    
    image_pairs = list(find_image_pair())
    if image_pairs:
        first_base, first_mask = image_pairs[0]
        return DoctorImageValidationResponse(
            id=None,
            image_path=os.path.join("images", first_base),
            mask_path=os.path.join("images", first_mask),
            doctor_name=None,
            rating=None,
            comments=None,
            mask_comments=None,
            disease_name="Unknown",  
            category=None
        )
    raise HTTPException(status_code=404, detail="No image pairs to categorize found.")


@app.get("/categorize_image/{current_displayed_filename}", response_model=Optional[DoctorImageValidationResponse])
async def get_next_uncategorized_image(current_displayed_filename: str):
    
    image_pairs = list(find_image_pair())
    current_base_filename, _ = os.path.splitext(current_displayed_filename)
    current_pair = None
    for base, mask in image_pairs:
        if os.path.splitext(base)[0] == current_base_filename:
            current_pair = (base, mask)
            break

    if current_pair:
        current_index = image_pairs.index(current_pair)
        if current_index < len(image_pairs) - 1:
            next_base, next_mask = image_pairs[current_index + 1]
            return DoctorImageValidationResponse(
                id=None,
                image_path=os.path.join("images", next_base),
                mask_path=os.path.join("images", next_mask),
                doctor_name=None,
                rating=None,
                comments=None,
                mask_comments=None,
                disease_name=None,
                category=None
            )
    elif image_pairs:
        first_base, first_mask = image_pairs[0]
        return DoctorImageValidationResponse(
            id=None,
            image_path=os.path.join("images", first_base),
            mask_path=os.path.join("images", first_mask),
            doctor_name=None,
            rating=None,
            comments=None,
            mask_comments=None,
            disease_name=None,
            category=None
        )
    return None

@app.post("/categorize_image/")
async def submit_categorization(
    current_filename: str = Form(...),  
    doctor_name: str = Form(...),  
    rating: int = Form(...),
    comments: Optional[str] = Form(None),
    mask_comments: Optional[str] = Form(None),
    disease_name: str = Form(...),
    category: str = Form(...),
    real_generated: str = Form(...),  
    realism_rating: Optional[int] = Form(None),  
    image_precision: str = Form(...),  
    skin_color_precision: Optional[int] = Form(None),  
    confidence_level: Optional[int] = Form(None),  
    crop_quality_rating: Optional[int] = Form(None),  
    crop_diagnosis: str = Form(...),  
    fitzpatrick_scale: Optional[str] = Form(None),  
    db: Session = Depends(get_db),
):
    
    base_name, ext = os.path.splitext(current_filename)
    original_filename = f"{base_name}{ext}"
    mask_filename = f"{base_name}_mask{ext}"

    db_image = DoctorImageValidation(
        image_path=os.path.join("images", original_filename),
        mask_path=os.path.join("images", mask_filename),
        doctor_name=doctor_name,
        rating=rating,
        comments=comments,
        mask_comments=mask_comments,
        disease_name=disease_name,
        category=category,
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    image_id = db_image.id

    source_original_path = os.path.join("images", original_filename)
    source_mask_path = os.path.join("images", mask_filename)
    destination_dir = os.path.join("images", category)
    os.makedirs(destination_dir, exist_ok=True)
    destination_original_path = os.path.join(destination_dir, original_filename)
    destination_mask_path = os.path.join(destination_dir, mask_filename)

    def move_file_with_collision_handling(source, destination):
        
        if os.path.exists(destination):
            name, ext = os.path.splitext(os.path.basename(source))
            counter = 1
            while True:
                new_filename = f"{name}_{counter}{ext}"
                new_destination = os.path.join(os.path.dirname(destination), new_filename)
                if not os.path.exists(new_destination):
                    destination = new_destination
                    return destination, new_filename
                counter += 1
        return destination, os.path.basename(source)

    try:
        new_original_path, new_original_filename = move_file_with_collision_handling(
            source_original_path, destination_original_path
        )
        new_mask_path, new_mask_filename = move_file_with_collision_handling(
            source_mask_path, destination_mask_path
        )
        os.rename(source_original_path, new_original_path)
        os.rename(source_mask_path, new_mask_path)

        db_image.image_path = os.path.join("images", category, new_original_filename)
        db_image.mask_path = os.path.join("images", category, new_mask_filename)
        db_image.real_generated = real_generated
        db_image.realism_rating = realism_rating
        db_image.image_precision = image_precision
        db_image.skin_color_precision = skin_color_precision
        db_image.confidence_level = confidence_level
        db_image.crop_quality_rating = crop_quality_rating
        db_image.crop_diagnosis = crop_diagnosis
        db_image.fitzpatrick_scale = fitzpatrick_scale

        db.commit()
        return {"message": f"Images categorized as {category} and moved.", "image_id": image_id}
    except FileNotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=f"Source file not found: {e.filename}")
    except Exception as e:
        db.rollback()
        logging.error(f"Error moving files: {e}")
        raise HTTPException(status_code=500, detail="Failed to move images")


@app.get("/disease_images/{disease_name}", response_model=List[DoctorImageValidationResponse])
async def get_disease_images(disease_name: str, db: Session = Depends(get_db)):
    
    images = db.query(DoctorImageValidation).filter(
        DoctorImageValidation.disease_name == disease_name
    ).all()
    return images


@app.post("/update_image_details/{image_id}")
async def update_image_details(
    image_id: int, 
    doctor_name: str = Form(...),
    rating: int = Form(...),
    comments: Optional[str] = Form(None),
    mask_comments: Optional[str] = Form(None),
    disease_name: str = Form(...),
    category: str = Form(...),
    real_generated: str = Form(...),  
    realism_rating: Optional[int] = Form(None),  
    image_precision: str = Form(...),  
    skin_color_precision: Optional[int] = Form(None),  
    confidence_level: Optional[int] = Form(None),  
    crop_quality_rating: Optional[int] = Form(None),  
    crop_diagnosis: str = Form(...),  
    fitzpatrick_scale: Optional[str] = Form(None), 
    db: Session = Depends(get_db),
):
    
    db_image = db.query(DoctorImageValidation).filter(DoctorImageValidation.id == image_id).first()
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")

    old_category = db_image.category  
    old_image_path = db_image.image_path
    old_mask_path = db_image.mask_path

    db_image.doctor_name = doctor_name
    db_image.rating = rating
    db_image.comments = comments
    db_image.mask_comments = mask_comments
    db_image.disease_name = disease_name
    db_image.category = category
    db_image.real_generated = real_generated 
    db_image.realism_rating = realism_rating 
    db_image.image_precision = image_precision 
    db_image.skin_color_precision = skin_color_precision 
    db_image.confidence_level = confidence_level 
    db_image.crop_quality_rating = crop_quality_rating 
    db_image.crop_diagnosis = crop_diagnosis 
    db_image.fitzpatrick_scale = fitzpatrick_scale 
    db.commit()  

    
    if old_category != category:
        try:
            
            source_original_path = os.path.join(old_image_path)
            source_mask_path = os.path.join(old_mask_path)
            destination_dir = os.path.join("images", category)  
            os.makedirs(destination_dir, exist_ok=True)
            destination_original_path = os.path.join(destination_dir, os.path.basename(old_image_path))
            destination_mask_path = os.path.join(destination_dir, os.path.basename(old_mask_path))

            def move_file_with_collision_handling(source, destination):
                
                if os.path.exists(destination):
                    name, ext = os.path.splitext(os.path.basename(source))
                    counter = 1
                    while True:
                        new_filename = f"{name}_{counter}{ext}"
                        new_destination = os.path.join(os.path.dirname(destination), new_filename)
                        if not os.path.exists(new_destination):
                            destination = new_destination
                            return destination, os.path.basename(new_filename)
                        counter += 1
                return destination, os.path.basename(source)

            new_original_path, new_original_filename = move_file_with_collision_handling(
                source_original_path, destination_original_path
            )
            new_mask_path, new_mask_filename = move_file_with_collision_handling(
                source_mask_path, destination_mask_path
            )
            os.rename(source_original_path, new_original_path)
            os.rename(source_mask_path, new_mask_path)

            
            db_image.image_path = os.path.join("images", category, new_original_filename)
            db_image.mask_path = os.path.join("images", category, new_mask_filename)
            db.commit()

        except FileNotFoundError as e:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Source file not found: {e.filename}")
        except Exception as e:
            db.rollback()
            logging.error(f"Error moving files: {e}")
            raise HTTPException(status_code=500, detail="Failed to move images")

    db.refresh(db_image)
    return {"message": "Image details updated successfully", "image_id": image_id}


@app.get("/download_excel/")
async def download_categorizations_excel(db: Session = Depends(get_db)):
    
    categorizations = db.query(DoctorImageValidation).all()
    if not categorizations:
        raise HTTPException(
            status_code=404, detail="No categorizations found in the database."
        )

    
    data = [entry.__dict__ for entry in categorizations]
    
    for row in data:
        row.pop('_sa_instance_state', None)

    df = pd.DataFrame(data)
    excel_file_path = "categorization_data.xlsx"
    df.to_excel(excel_file_path, index=False)

    return FileResponse(
        excel_file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="categorization_data.xlsx",
    )



@app.get("/filter_entries/", response_model=List[DoctorImageValidationResponse])
async def filter_categorizations(
    category: str = Query(...),
    disease_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    
    query = db.query(DoctorImageValidation).filter(DoctorImageValidation.category == category)
    if disease_name:
        query = query.filter(DoctorImageValidation.disease_name == disease_name)
    results = query.all()

    formatted_results = [
        DoctorImageValidationResponse(
            id=result.id,
            image_path=result.image_path,
            mask_path=result.mask_path,
            doctor_name=result.doctor_name,
            rating=result.rating,
            comments=result.comments,
            mask_comments=result.mask_comments,
            disease_name=result.disease_name,
            category=result.category,
            created_at=result.created_at,
        )
        for result in results
    ]
    return formatted_results


@app.get("/all_categorizations/", response_model=List[DoctorImageValidationResponse])
async def get_all_categorizations(db: Session = Depends(get_db)):
    
    return db.query(DoctorImageValidation).all()


@app.get("/disease_names/", response_model=List[str])
async def get_disease_names(db: Session = Depends(get_db)):
    
    disease_names = db.query(DoctorImageValidation.disease_name).distinct().all()
    return [row[0] for row in disease_names]

@app.post("/register_doctor/")
async def register_doctor(
    doctorName: str = Form(...),
    hospital: Optional[str] = Form(None),
    hospitalAddress: Optional[str] = Form(None),
    contactNumber: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    specialization: Optional[str] = Form(None),
    registrationId: str = Form(...),
    yearsOfExperience: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    if db.query(Doctor).filter(Doctor.registration_id == registrationId).first():
        raise HTTPException(status_code=400, detail="Registration ID already exists")

    db_doctor = Doctor(
        doctor_name=doctorName,
        hospital=hospital,
        hospital_address=hospitalAddress,
        contact_number=contactNumber,
        email=email,
        specialization=specialization,
        registration_id=registrationId,
        years_of_experience=yearsOfExperience,
    )

    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)

    return {"message": "Doctor registered successfully", "doctor_id": db_doctor.id}



###----------------------------------------Get Doctors from the DB--------------------------------------------------------###
@app.get("/doctors/", response_model=List[DoctorSchema])
async def get_doctors(db: Session = Depends(get_db)):
    doctors = db.query(Doctor).all()
    return doctors
###-----------------------------------------------------------------------------------------------------------------------###


@app.delete("/delete_table/{table_name}")
def delete_table_route(table_name: str, db: Session = Depends(get_db)):
    
    if table_name not in ('doctor_image_validation', 'doctors', 'skin_disease_image', 'crop_image_validation', 'crop_image_quality_rating', 'crop_image_rating'):
        raise HTTPException(
            status_code=400,
            detail="Invalid table name. Must be 'doctor_image_validation', 'doctors', 'skin_disease_image', 'crop_image_validation', 'crop_image_quality_rating'\
                          'crop_image_rating'.",
        )

    try:
        db.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        db.commit()  # Commit the transaction after dropping the table
        return {"message": f"Table '{table_name}' has been deleted."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while deleting the table: {str(e)}",
        )


def populate_database_from_filesystem(db: Session, image_root: str):

    
    
    for amended_dir in os.listdir(image_root):
        amended_path = os.path.join(image_root, amended_dir)
        if not os.path.isdir(amended_path):
            continue

        for disease_dir in os.listdir(amended_path):
            disease_path = os.path.join(amended_path, disease_dir)
            if not os.path.isdir(disease_path):
                continue

            for persona_dir in os.listdir(disease_path):
                if not persona_dir.startswith("persona"):
                    continue

                persona_digits = persona_dir[len("persona"):]
                persona_path = os.path.join(disease_path, persona_dir)
                if not os.path.isdir(persona_path):
                    continue

                for example_dir in os.listdir(persona_path):
                    if not example_dir.startswith("example"):
                        continue

                    example_digit = example_dir[len("example"):]
                    example_path = os.path.join(persona_path, example_dir)
                    if not os.path.isdir(example_path):
                        continue

                    for filename in os.listdir(example_path):
                        #
                        if "_crop" in filename or not filename.endswith(".png"):
                            continue

                        relative_path = os.path.join(amended_dir, disease_dir, persona_dir, example_dir, filename)
                        full_path = os.path.join(image_root, relative_path)

                        if "_mask" in filename:
                            
                            match = re.match(r"(.+)_mask\.png$", filename)
                            if not match:
                                print(f"Invalid mask filename: {filename}")
                                continue

                            base_image_name = match.group(1) + ".png"
                            print(f"Processing mask: {filename}, base_image_name: {base_image_name}")

                            
                            original_image = db.query(SkinDiseaseImage).filter_by(
                                disease_name_amended=amended_dir,
                                disease_name=disease_dir,
                                persona_digits=persona_digits,
                                example_digit=example_digit,
                                image_name=base_image_name
                            ).first()

                            if original_image:
                                original_image.mask_name = filename
                                original_image.mask_path = os.path.join("/skin_disease_data", relative_path)
                                print(f"Linked mask {filename} to image {base_image_name}")
                            else:
                                print(f"No image found for mask: {filename} (expected image: {base_image_name})")
                        else:
                            
                            new_image = SkinDiseaseImage(
                                disease_name_amended=amended_dir,
                                disease_name=disease_dir,
                                persona_digits=persona_digits,
                                example_digit=example_digit,
                                image_name=filename,
                                image_path=os.path.join("/skin_disease_data", relative_path)
                            )
                            
                            mask_filename = filename.replace(".png", "_mask.png")
                            mask_path = os.path.join(example_path, mask_filename)
                            if os.path.exists(mask_path):
                                new_image.mask_name = mask_filename
                                new_image.mask_path = os.path.join("/skin_disease_data", amended_dir, disease_dir, persona_dir, example_dir, mask_filename)

                            db.add(new_image)
                            print(f"Added image: {filename}")
    db.commit()


@app.post("/populate_database/")
async def populate_db(db: Session = Depends(get_db), image_path: str = Query(..., description="Absolute path to the skin disease image directory")):
    populate_database_from_filesystem(db, image_root=image_path)
    return {"message": f"Database populated from filesystem at {image_path}."}



@app.get("/skin_disease_images/", response_model=List[SkinDiseaseImageResponse])
async def get_skin_disease_images(db: Session = Depends(get_db), page: int = 1, per_page: int = 1):
    skip = (page - 1) * per_page
    images = db.query(SkinDiseaseImage).offset(skip).limit(per_page).all()
    return images

@app.get("/skin_disease_images/{image_id}", response_model=Optional[SkinDiseaseImageResponse])
async def get_skin_disease_image(image_id: int, db: Session = Depends(get_db)):
    image = db.query(SkinDiseaseImage).filter(SkinDiseaseImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@app.get("/unique_patients/", response_model=List[str])
async def get_unique_patients(
    validation_status: Optional[str] = Query("all", description="Filter by validation status: 'all', 'validated', 'unvalidated'"),
    db: Session = Depends(get_db)
):
    
    query = db.query(SkinDiseaseImage.persona_digits)

    if validation_status == "validated":
        
        query = query.filter(SkinDiseaseImage.doctor_name.isnot(None), SkinDiseaseImage.doctor_name != '')
    elif validation_status == "unvalidated":
        
        query = query.filter(or_(SkinDiseaseImage.doctor_name.is_(None), SkinDiseaseImage.doctor_name == ''))
    

    unique_personas = query.distinct().all()
    
    return sorted([persona[0] for persona in unique_personas if persona[0] is not None])
from sqlalchemy.sql import or_


# @app.get("/patient_images/{persona_digits}", response_model=List[PatientImageMetadata])
# async def get_patient_images(
#     persona_digits: str,
#     validation_status: Optional[str] = Query("all", description="Filter by validation status: 'all', 'validated', 'unvalidated'"),
#     db: Session = Depends(get_db)
# ):
    
#     query = db.query(SkinDiseaseImage).filter(
#         SkinDiseaseImage.persona_digits == persona_digits
#     )

#     if validation_status == "validated":
#         query = query.filter(SkinDiseaseImage.doctor_name.isnot(None), SkinDiseaseImage.doctor_name != '')
#     elif validation_status == "unvalidated":
#         query = query.filter(or_(SkinDiseaseImage.doctor_name.is_(None), SkinDiseaseImage.doctor_name == ''))
    
#     images_from_db = query.all()

#     if not images_from_db:
#         raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="No images found for this patient with the specified validation status in the database.")

#     images_data = []
#     for img_entry in images_from_db:
#         images_data.append(PatientImageMetadata(
#             image_path=img_entry.image_path,
#             image_name=img_entry.image_name,
#             mask_path=img_entry.mask_path,
#             mask_name=img_entry.mask_name
#         ))
    
#     images_data.sort(key=lambda x: x.image_name) 
    
#     return images_data


@app.get("/patient_images/{persona_digits}", response_model=List[PatientImageMetadata])
async def get_patient_images(
    persona_digits: str,
    validation_status: Optional[str] = Query("all", description="Filter by validation status: 'all', 'validated', 'unvalidated'"),
    db: Session = Depends(get_db)
):
    query = db.query(SkinDiseaseImage).filter(
        SkinDiseaseImage.persona_digits == persona_digits
    )

    if validation_status == "validated":
        query = query.filter(SkinDiseaseImage.doctor_name.isnot(None), SkinDiseaseImage.doctor_name != '')
    elif validation_status == "unvalidated":
        query = query.filter(or_(SkinDiseaseImage.doctor_name.is_(None), SkinDiseaseImage.doctor_name == ''))

    images_from_db = query.all()

    if not images_from_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, 
            detail="No images found for this patient with the specified validation status in the database."
        )

    # ✅ Deduplicate by image_path (keep first entry)
    unique_images = {}
    for img_entry in images_from_db:
        if img_entry.image_path not in unique_images:
            unique_images[img_entry.image_path] = PatientImageMetadata(
                image_path=img_entry.image_path,
                image_name=img_entry.image_name,
                mask_path=img_entry.mask_path,
                mask_name=img_entry.mask_name
            )

    images_data = list(unique_images.values())
    images_data.sort(key=lambda x: x.image_name)

    return images_data




# @app.post("/classify_skin_tone/{persona_digits}", response_model=SkinToneClassificationResponse, status_code=HTTPStatus.CREATED)
# async def classify_skin_tone(
#     persona_digits: str,
#     classification_data: SkinToneClassificationRequest, 
#     db: Session = Depends(get_db)
# ):
    
#     try:
        

#         skin_disease_images = db.query(SkinDiseaseImage).filter(
#             SkinDiseaseImage.persona_digits == persona_digits
#         ).all()

#         if not skin_disease_images:
#             raise HTTPException(
#                 status_code=HTTPStatus.NOT_FOUND,
#                 detail=f"No SkinDiseaseImage entries found for persona_digits {persona_digits}."
#             )

#         updated_count = 0
#         created_count = 0

#         for image_entry in skin_disease_images:
            
#             image_name_log = image_entry.image_name
#             image_path_log = image_entry.image_path
#             mask_name_log = image_entry.mask_name
#             mask_path_log = image_entry.mask_path
#             crop_image_name_log = image_entry.crop_image_name
#             crop_image_path_log = image_entry.crop_image_path
#             crop_mask_name_log = image_entry.crop_mask_name
#             crop_mask_path_log = image_entry.crop_mask_path

#             # Always create a new entry in SkinToneClassification (logging each classification event)
#             # new_classification_log = SkinToneClassification(
#             #     persona_digits=persona_digits,
#             #     doctor_name=classification_data.doctor_name,
#             #     fitzpatrick_scale=classification_data.fitzpatrick_scale,
#             #     image_name=image_name_log,
#             #     image_path=image_path_log,
#             #     mask_name=mask_name_log,
#             #     mask_path=mask_path_log,
#             #     crop_image_name=crop_image_name_log,
#             #     crop_image_path=crop_image_path_log,
#             #     crop_mask_name=crop_mask_name_log,
#             #     crop_mask_path=crop_mask_path_log
#             # )
#             # db.add(new_classification_log)

            
#             if image_entry.doctor_name is None or image_entry.doctor_name == "":
                
#                 image_entry.doctor_name = classification_data.doctor_name
#                 image_entry.fitzpatrick_scale = classification_data.fitzpatrick_scale
#                 image_entry.confidence_level = classification_data.confidence
#                 updated_count += 1
#                 print(f"Updated existing SkinDiseaseImage ID {image_entry.id} for {image_entry.image_name}")
#             else:
                
#                 new_skin_disease_image_entry = SkinDiseaseImage(
#                     disease_name_amended=image_entry.disease_name_amended,
#                     disease_name=image_entry.disease_name,
#                     persona_digits=image_entry.persona_digits,
#                     example_digit=image_entry.example_digit,
#                     image_name=image_entry.image_name,
#                     mask_name=image_entry.mask_name,
#                     image_path=image_entry.image_path,
#                     mask_path=image_entry.mask_path,
#                     crop_image_name=image_entry.crop_image_name,
#                     crop_image_path=image_entry.crop_image_path,
#                     crop_mask_name=image_entry.crop_mask_name,
#                     crop_mask_path=image_entry.crop_mask_path,
                    
#                     doctor_name=classification_data.doctor_name,
#                     fitzpatrick_scale=classification_data.fitzpatrick_scale,
#                     confidence_level = classification_data.confidence,
                    
#                     rating=image_entry.rating,
#                     comments=image_entry.comments,
#                     category=image_entry.category,
#                     years_of_experience=image_entry.years_of_experience,
#                     real_generated=image_entry.real_generated,
#                     realism_rating=image_entry.realism_rating,
#                     image_precision=image_entry.image_precision,
#                     skin_color_precision=image_entry.skin_color_precision,
#                     #confidence_level=image_entry.confidence_level,
#                     crop_quality_rating=image_entry.crop_quality_rating,
#                     crop_diagnosis=image_entry.crop_diagnosis,
#                     created_at=datetime.now(ZoneInfo("Europe/Rome"))
#                 )
#                 db.add(new_skin_disease_image_entry)
#                 created_count += 1
#                 print(f"Created new SkinDiseaseImage entry for {image_entry.image_name} with ID {new_skin_disease_image_entry.id}")

#         db.commit()

#         return {"message": f"Classification submitted for patient {persona_digits}. {updated_count} existing records updated, {created_count} new records created."}

#     except Exception as e:
#         db.rollback()
#         print(f"Error classifying skin tone for {persona_digits}: {e}")
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail=f"An unexpected error occurred during classification: {e}"
#         )


@app.post("/classify_skin_tone/{persona_digits}", response_model=SkinToneClassificationResponse, status_code=HTTPStatus.CREATED)
async def classify_skin_tone(
    persona_digits: str,
    classification_data: SkinToneClassificationRequest, 
    db: Session = Depends(get_db)
):
    try:
        skin_disease_images = db.query(SkinDiseaseImage).filter(
            SkinDiseaseImage.persona_digits == persona_digits
        ).all()

        if not skin_disease_images:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"No SkinDiseaseImage entries found for persona_digits {persona_digits}."
            )

        updated_count = 0
        created_count = 0
        processed_images = set()  

        for image_entry in skin_disease_images:
            if image_entry.image_path in processed_images:
                continue
            processed_images.add(image_entry.image_path)

            if not image_entry.doctor_name:  # None or empty
                image_entry.doctor_name = classification_data.doctor_name
                image_entry.fitzpatrick_scale = classification_data.fitzpatrick_scale
                image_entry.confidence_level = classification_data.confidence
                updated_count += 1
                print(f"Updated SkinDiseaseImage ID {image_entry.id} for {image_entry.image_name}")
            else:
                new_skin_disease_image_entry = SkinDiseaseImage(
                    disease_name_amended=image_entry.disease_name_amended,
                    disease_name=image_entry.disease_name,
                    persona_digits=image_entry.persona_digits,
                    example_digit=image_entry.example_digit,
                    image_name=image_entry.image_name,
                    mask_name=image_entry.mask_name,
                    image_path=image_entry.image_path,
                    mask_path=image_entry.mask_path,
                    crop_image_name=image_entry.crop_image_name,
                    crop_image_path=image_entry.crop_image_path,
                    crop_mask_name=image_entry.crop_mask_name,
                    crop_mask_path=image_entry.crop_mask_path,

                    doctor_name=classification_data.doctor_name,
                    fitzpatrick_scale=classification_data.fitzpatrick_scale,
                    confidence_level=classification_data.confidence,

                    rating=image_entry.rating,
                    comments=image_entry.comments,
                    category=image_entry.category,
                    years_of_experience=image_entry.years_of_experience,
                    real_generated=image_entry.real_generated,
                    realism_rating=image_entry.realism_rating,
                    image_precision=image_entry.image_precision,
                    skin_color_precision=image_entry.skin_color_precision,
                    crop_quality_rating=image_entry.crop_quality_rating,
                    crop_diagnosis=image_entry.crop_diagnosis,
                    created_at=datetime.now(ZoneInfo("Europe/Rome"))
                )
                db.add(new_skin_disease_image_entry)
                created_count += 1
                print(f"Created new SkinDiseaseImage entry for {image_entry.image_name}")

        db.commit()

        return {"message": f"Classification submitted for patient {persona_digits}. "
                           f"{updated_count} unique records updated, {created_count} new records created."}

    except Exception as e:
        db.rollback()
        print(f"Error classifying skin tone for {persona_digits}: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during classification: {e}"
        )




@app.get("/check_skin_disease_images/", response_model=List[SkinDiseaseImageResponse])
async def get_skin_disease_image_contents(db: Session = Depends(get_db)):
    
    contents = db.query(SkinDiseaseImage).all()
    return contents

@app.get("/download_skin_disease_excel/")
async def download_skin_disease_excel(db: Session = Depends(get_db)):
    
    images = db.query(SkinDiseaseImage).all()
    if not images:
        raise HTTPException(status_code=404, detail="No entries found in the skin disease table.")

    
    column_names = [column.name for column in SkinDiseaseImage.__table__.columns]
    data = [{col: getattr(image, col) for col in column_names} for image in images]

    df = pd.DataFrame(data)

    excel_file_path = "skin_disease_images.xlsx"
    df.to_excel(excel_file_path, index=False)

    return FileResponse(
        excel_file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="skin_disease_images.xlsx",
    )


@app.get("/skin_disease_image/export_excel")
def export_categorize_excel(db: Session = Depends(get_db)):
    images = db.query(DoctorImageValidation).all()
    if not images:
        raise HTTPException(status_code=404, detail="No entries found in the skin disease table.")

    
    column_names = [column.name for column in DoctorImageValidation.__table__.columns]
    data = [{col: getattr(image, col) for col in column_names} for image in images]

    df = pd.DataFrame(data)

    excel_file_path = "skin_disease_images.xlsx"
    df.to_excel(excel_file_path, index=False)

    return FileResponse(
        excel_file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="skin_ctaegorize_images.xlsx",
    )


@app.post("/populate_crops_single_table/")
def populate_crop_data_flat(image_root: str, db: Session = Depends(get_db)):
    
    for amended_dir in os.listdir(image_root):
        amended_path = os.path.join(image_root, amended_dir)
        if not os.path.isdir(amended_path):
            continue

        for disease_dir in os.listdir(amended_path):
            disease_path = os.path.join(amended_path, disease_dir)
            if not os.path.isdir(disease_path):
                continue

            for persona_dir in os.listdir(disease_path):
                if not persona_dir.startswith("persona"):
                    continue
                persona_digits = persona_dir[len("persona"):]
                persona_path = os.path.join(disease_path, persona_dir)

                for example_dir in os.listdir(persona_path):
                    if not example_dir.startswith("example"):
                        continue
                    example_digit = example_dir[len("example"):]
                    example_path = os.path.join(persona_path, example_dir)


                    
                    for filename in os.listdir(example_path):
                        if not (filename.endswith(".png") or filename.endswith(".jpg")):
                            continue

                        if "_crop" not in filename:
                            continue

                        is_mask = "_mask" in filename
                        relative_path = os.path.join(amended_dir, disease_dir, persona_dir, example_dir, filename)

                        
                        base_image_name = filename.replace("_crop", "").replace("_mask", "")

                        
                        entry = db.query(SkinDiseaseImage).filter_by(
                            disease_name_amended=amended_dir,
                            disease_name=disease_dir,
                            persona_digits=persona_digits,
                            example_digit=example_digit,
                            image_name=base_image_name
                        ).first()

                        if entry:
                            if is_mask:
                                entry.crop_mask_name = filename
                                entry.crop_mask_path = os.path.join("/skin_disease_data", relative_path)
                            else:
                                entry.crop_image_name = filename
                                entry.crop_image_path = os.path.join("/skin_disease_data", relative_path)

    db.commit()
    return {"message": "Crop image and mask fields updated where filenames contain '_crop' and match image_name."}

from pydantic import BaseModel


class UpdateImageFields(BaseModel):
    crop_quality_rating: Optional[int] = None
    crop_diagnosis: Optional[str] = None

@app.put("/update_image/{image_id}")
async def update_image_fields(image_id: int, update_data: UpdateImageFields, db: Session = Depends(get_db)):
    image = db.query(SkinDiseaseImage).filter(SkinDiseaseImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    if update_data.crop_quality_rating is not None:
        image.crop_quality_rating = update_data.crop_quality_rating
    if update_data.crop_diagnosis is not None:
        image.crop_diagnosis = update_data.crop_diagnosis

    db.commit()
    db.refresh(image)
    return {"message": "Image updated successfully"}


router = APIRouter()
BASE_IMAGE_DIR = "images"
DISEASE_DIR = os.path.join(BASE_IMAGE_DIR, "disease")
NON_DISEASE_DIR = os.path.join(BASE_IMAGE_DIR, "non-disease")


def move_and_rename_file(src_path: str, dest_dir: str) -> str:
    
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    base_name = os.path.basename(src_path)
    name, ext = os.path.splitext(base_name)
    dest_path = os.path.join(dest_dir, base_name)

    suffix = 1
    while os.path.exists(dest_path):
        new_name = f"{name}_{suffix}{ext}"
        dest_path = os.path.join(dest_dir, new_name)
        suffix += 1

    shutil.move(src_path, dest_path)
    return os.path.basename(dest_path) 


# const payload = {
#                 doctor_name: doctorNameInput.value,
#                 comments: commentsInput.value,
#                 mask_comments: maskCommentsInput.value,
#                 //category: categorySelect.value,
#                 real_generated: getRadioValue('real_generated'), // Now a number (1 or 2)
#                 realism_rating: getRadioValue('realism_rating'),
#                 mask_rating: getRadioValue('mask_rating'), // New field
#                 image_precision: getSelectValue('image_precision'),
#                 confidence_level: getRadioValue('confidence_level'),
#                 // Removed: disease_name, skin_color_precision, crop_quality_rating, crop_diagnosis, fitzpatrick_scale
#                 // Image paths are handled by the backend based on base_name, not sent in payload for this endpoint
#             };


router = APIRouter()
IMAGE_DIR = "/images/categorized_images"


################ -------------------------------------   CATEGRIZE IMAGES MODULE --------------------------------########################
BASE_IMAGE_DIR = "images"
# Source Directory for Images for Categorize_images Module
CATEGORIZE_IMAGES_DIRECTORY = os.path.join(BASE_IMAGE_DIR, "categorized_images")
os.makedirs(CATEGORIZE_IMAGES_DIRECTORY, exist_ok=True)
# Target Directory for Images for Categorize_images Module
CATEGORIZE_IMAGES_DIRECTORY_TARGET = os.path.join(BASE_IMAGE_DIR, "categorized_images_crops_categorized")
os.makedirs(CATEGORIZE_IMAGES_DIRECTORY_TARGET, exist_ok=True)


def move_to_target_directory_with_unique_name(src_path: str, target_dir: str):
    
    # Checking if it is absolute path
    #os.path.join(os.getcwd(), path)
    src_path = os.path.abspath(src_path)
    if not os.path.exists(src_path):
        print(f"Source file not found for moving: {src_path}")
        return None, None
    
    os.makedirs(target_dir, exist_ok=True)

    base_name = os.path.basename(src_path)
    name, ext = os.path.splitext(base_name)
    dest_path = os.path.join(target_dir, base_name)
    counter = 1

    while os.path.exists(dest_path):
        new_name = f"{name}_{counter}{ext}"
        dest_path = os.path.join(target_dir, new_name)
        counter += 1

    shutil.move(src_path, dest_path)
    
    return os.path.basename(dest_path), dest_path

# CATEGORIZE IMAGES (CATEGORIZE_IMAGES.HTML)
@app.get("/get_all_base_names")
async def get_all_base_names():
    try:
        files_list = os.listdir(CATEGORIZE_IMAGES_DIRECTORY)
        files_set = set(files_list)

        base_names_set = set()

        for file_ in files_list:
            if file_.endswith("_crop.jpg"):
                base_name = file_.replace("_crop.jpg", "")
                crop_mask = f"{base_name}_crop_mask.jpg"
                if crop_mask in files_set:
                    base_names_set.add(base_name)

        return JSONResponse(content=sorted(base_names_set))

    except Exception as error_:
        return JSONResponse(content={"error": str(error_)}, status_code=500)


@app.post("/skin_disease_image/update/{base_name}", response_model=DoctorImageValidationResponse)
def submit_validation(
    base_name: str, 
    payload: DoctorImageValidationRequest,
    db: Session = Depends(get_db)
):
    print(payload)

    
    crop_image_src_file = os.path.join(BASE_IMAGE_DIR, f"categorized_images/{base_name}_crop.jpg")
    crop_mask_src_file = os.path.join(BASE_IMAGE_DIR, f"categorized_images/{base_name}_crop_mask.jpg")

    
    #crop_new_filename, crop_abs_path = move_to_target_directory_with_unique_name(crop_image_src_file, CATEGORIZE_IMAGES_DIRECTORY_TARGET)
    #crop_mask_new_filename, crop_mask_abs_path = move_to_target_directory_with_unique_name(crop_mask_src_file, CATEGORIZE_IMAGES_DIRECTORY_TARGET)

    #crop_db_path = f"/images/categorized_images_crops_categorized/{crop_new_filename}" if crop_new_filename else None
    #crop_mask_db_path = f"/images/categorized_images_crops_categorized/{crop_mask_new_filename}" if crop_mask_new_filename else None

    
    db_row = DoctorImageValidation(
        image_path=None,
        mask_path=None,
        crop_path=f"/images/categorized_images/{base_name}_crop.jpg", #crop_db_path,
        crop_mask_path=f"/images/categorized_images/{base_name}_crop_mask.jpg", #crop_mask_db_path,
        doctor_name=payload.doctor_name, #--------------DONE
        mask_rating=payload.mask_rating,   #--------------DONE
        comments=payload.comments,   #--------------DONE
        mask_comments=payload.mask_comments,   #--------------DONE
        disease_name=None,
        category=None,
        real_generated=payload.real_generated,   #--------------DONE
        realism_rating=payload.realism_rating,   #--------------DONE
        image_precision=payload.image_precision,   #--------------DONE
        skin_color_precision=None,
        confidence_level=payload.confidence_level,   #--------------DONE
        crop_quality_rating=None,
        crop_diagnosis=None,
        fitzpatrick_scale=None,
        created_at=datetime.now(ZoneInfo("Europe/Rome"))
    )

    # from datetime import datetime
    # from zoneinfo import ZoneInfo
    # server_timezone = "America/New_York"
    # new_timezone = "Europe/Rome"
    # current_time = datetime.now(ZoneInfo(server_timezone)) 
    # current_time_in_new_timezone = current_time.astimezone(ZoneInfo(new_timezone))
    # print(current_time.isoformat(timespec='seconds'))
    # # 2024-04-18T02:37:10-04:00
    # print(repr(current_time))
    # # datetime.datetime(2024, 4, 18, 2, 37, 10, 30703, tzinfo=zoneinfo.ZoneInfo(key='America/New_York'))
    # print(current_time_in_new_timezone.isoformat(timespec='seconds'))
    # # 2024-04-17T23:37:10-07:00

    print(payload)
    db.add(db_row)
    db.commit()
    db.refresh(db_row)

    return db_row

#################--------------------------------------------------------------------------------------------------##########################


@app.get("/get_image_set/{image_name}")
async def get_image_set(image_name: str):
    base_dir = "path/to/your/images"  
    
    image_set = {
        "original": f"{image_name}.jpg",  
        "original_mask": f"{image_name}_mask.jpg",
        "crop": f"{image_name}_crop.jpg",
        "crop_mask": f"{image_name}_crop_mask.jpg"
    }

    image_urls = {}
    for key, filename in image_set.items():
        file_path = os.path.join(base_dir, filename)
        if os.path.exists(file_path):
            image_urls[key] = f"/static/images/{filename}" 
        else:
            image_urls[key] = None  

    return JSONResponse(content=image_urls)

@app.get("/get_skin_disease_data/") 
async def get_skin_disease_data(db: Session = Depends(get_db)):
    
    images = db.query(SkinDiseaseImage).all()
    if not images:
        raise HTTPException(status_code=404, detail="No entries found in the skin disease table.")

    
    data = []
    for image in images:
        data.append({
            "id": image.id,
            "disease_name_amended": image.disease_name_amended,
            "disease_name": image.disease_name,
            "persona_digits": image.persona_digits,
            "example_digit": image.example_digit,
            "image_name": image.image_name,
            "mask_name": image.mask_name,
            "image_path": image.image_path,
            "mask_path": image.mask_path,
            "crop_image_name": image.crop_image_name,
            "crop_image_path": image.crop_image_path,
            "crop_mask_name": image.crop_mask_name,
            "crop_mask_path": image.crop_mask_path,
            "doctor_name": image.doctor_name,
            "rating": image.rating,
            "comments": image.comments,
            "category": image.category,
            "years_of_experience": image.years_of_experience,
            "real_generated": image.real_generated,
            "realism_rating": image.realism_rating,
            "image_precision": image.image_precision,
            "skin_color_precision": image.skin_color_precision,
            "confidence_level": image.confidence_level,
            "crop_quality_rating": image.crop_quality_rating,
            "crop_diagnosis": image.crop_diagnosis,
            "fitzpatrick_scale": image.fitzpatrick_scale,
            "created_at": image.created_at.isoformat() if image.created_at else None
        })

    return JSONResponse(content=data)


@app.get("/get_categorized_excel_data/")
def get_categorized_excel_data(db: Session = Depends(get_db)):
    
    images = db.query(DoctorImageValidation).all()
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No entries found in the doctor image validation table.")

    
    column_names = [column.name for column in DoctorImageValidation.__table__.columns]
    data = []
    for image in images:
        row_data = {}
        for col_name in column_names:
            value = getattr(image, col_name)
            if isinstance(value, datetime):
                row_data[col_name] = value.isoformat()
            else:
                row_data[col_name] = value
        data.append(row_data)

    return JSONResponse(content=data)


from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os

#router = APIRouter()

IMAGE_DIR = "images"
image_index = {"index": 0}

@app.get("/categorize_image/")
async def get_next_image():
    all_files = sorted(f for f in os.listdir(IMAGE_DIR) if f.endswith((".png", ".jpg")))
    base_names = sorted(set(f.split("_mask")[0].split("_crop")[0] for f in all_files))

    if image_index["index"] >= len(base_names):
        return JSONResponse(content={"message": "No more images"}, status_code=404)

    base_name = base_names[image_index["index"]]
    image_index["index"] += 1

    return {
        "filename": base_name
    }

@app.post("/categorize_image/reset")
def reset_index():
    image_index["index"] = 0
    return {"message": "Index reset"}



##### ------------------------------------------------------CATEGORIZED IMAGES CROPS BATCH----------------------------------------------------###########

import logging
logger = logging.getLogger(__name__)

CATEGORIZE_IMAGES_CROPS_BATCH_SOURCE_DIR = os.path.join(BASE_IMAGE_DIR, "categorize_images_crops")
CATEGORIZE_IMAGES_CROPS_BATCH_TARGET_DIR = os.path.join(BASE_IMAGE_DIR, "categorized_images_crops_categorized")
os.makedirs(CATEGORIZE_IMAGES_CROPS_BATCH_SOURCE_DIR, exist_ok=True)
os.makedirs(CATEGORIZE_IMAGES_CROPS_BATCH_TARGET_DIR, exist_ok=True)


@app.get("/get_crop_image_batch", response_model=List[str])
async def get_crop_image_batch(db: Session = Depends(get_db)):     
    try:
     
        if not os.path.exists(CATEGORIZE_IMAGES_CROPS_BATCH_SOURCE_DIR):
            logger.error(f"Image directory does NOT exist: {CATEGORIZE_IMAGES_CROPS_BATCH_SOURCE_DIR}")
            raise HTTPException(status_code=500, detail=f"Image directory not found: {CATEGORIZE_IMAGES_CROPS_BATCH_SOURCE_DIR}")

        all_image_filenames = [
            f for f in os.listdir(CATEGORIZE_IMAGES_CROPS_BATCH_SOURCE_DIR)
            if os.path.isfile(os.path.join(CATEGORIZE_IMAGES_CROPS_BATCH_SOURCE_DIR, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]
        all_image_filenames.sort()

        return all_image_filenames 

    except Exception as error_:
        logger.exception("Error in get_crop_image_batch endpoint:")
        raise HTTPException(status_code=500, detail=f"Error retrieving image batch: {str(error_)}")


@app.post("/submit_batch_categorization", response_model=List[CropImageValidationResponse])
def submit_batch_categorization(
    payloads: List[CropImageValidationRequest],
    db: Session = Depends(get_db)
):

    records_to_add = []
    
    for payload in payloads:
        original_filename = payload.image_filename
        src_path = os.path.join(CATEGORIZE_IMAGES_CROPS_BATCH_SOURCE_DIR, original_filename)

        # if not os.path.exists(src_path):
        #     print(f"Warning: Image {original_filename} not found at {src_path}. Skipping.")
        #     continue # Skip

        # new_filename, new_abs_path = move_to_target_directory_with_unique_name(src_path, CATEGORIZE_IMAGES_CROPS_BATCH_TARGET_DIR)

        # if not new_filename:
        #     print(f"Could not move the file {original_filename}.")
        #     continue

        #image_db_path = f"/images/categorized_images_crops_categorized/{new_filename}"

        image_db_path = src_path

        db_record = CropImageValidation(
            image_filename = payload.image_filename,
            image_path=image_db_path,
            doctor_name=payload.doctor_name,
            comments=payload.comments,
            crop_diagnosis=payload.crop_diagnosis,
            fitzpatrick_scale=payload.fitzpatrick_scale,
            confidence=payload.confidence,
            created_at=datetime.now(ZoneInfo("Europe/Rome"))
        )
        records_to_add.append(db_record)

    try:
        
        db.add_all(records_to_add) 
        db.commit()
        
        responses_to_return = []
        for record in records_to_add:
            
            db.refresh(record) 

            
            responses_to_return.append(
                CropImageValidationResponse(
                    id=record.id,
                    image_filename=os.path.basename(record.image_filename), 
                    image_path=record.image_path,
                    doctor_name=record.doctor_name,
                    comments=record.comments,
                    crop_diagnosis=record.crop_diagnosis,
                    fitzpatrick_scale=record.fitzpatrick_scale,
                    confidence=record.confidence,
                    created_at=record.created_at
                )
            )
        
        return responses_to_return 

    except Exception as error_:
        db.rollback()
        print(f"Database transaction failed: {error_}")
        raise HTTPException(status_code=500, detail=f"Database error during batch submission: {error_}")


#########-----------------------------------------------------------------------------------------------------------------------------------###########


@app.get("/get_excel_data_categorized_images_crops_batch/")
def get_categorized_excel_data(db: Session = Depends(get_db)):
    
    images = db.query(CropImageValidation).all()
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No entries found in the doctor image validation table.")
    
    column_names = [column.name for column in CropImageValidation.__table__.columns]
    data = []
    for image in images:
        row_data = {}
        for col_name in column_names:
            value = getattr(image, col_name)
            if isinstance(value, datetime):
                row_data[col_name] = value.isoformat()
            else:
                row_data[col_name] = value
        data.append(row_data)

    return JSONResponse(content=data)

@app.post("/create_new_categorization/", response_model=DoctorImageValidationResponse)
async def create_new_categorization(
    data: DoctorImageValidationRequest, 
    db: Session = Depends(get_db),
):
    
    new_db_entry = DoctorImageValidation(
        image_path=None,#data.image_path, 
        mask_path=None,#data.mask_path,
        crop_path=data.crop_path,
        crop_mask_path=data.crop_mask_path,
        doctor_name=data.doctor_name,
        mask_rating = data.mask_rating,
        comments=data.comments,
        mask_comments=data.mask_comments,
        disease_name=None,#data.disease_name,
        category=None,#data.category,
        real_generated=data.real_generated,
        realism_rating=data.realism_rating,
        image_precision=data.image_precision,
        skin_color_precision=None,#data.skin_color_precision,
        confidence_level=data.confidence_level,
        crop_quality_rating=None,#data.crop_quality_rating,
        crop_diagnosis=None,#data.crop_diagnosis,
        fitzpatrick_scale=None,#data.fitzpatrick_scale,
        created_at=datetime.now(ZoneInfo("Europe/Rome"))
    )

    db.add(new_db_entry)
    db.commit()
    db.refresh(new_db_entry)

    return new_db_entry



CROP_IMAGES_SOURCE_DIR = os.path.join("images", "classify_skin_disease_crops_images")
CATEGORIZED_CROP_IMAGES_DIR = os.path.join(CROP_IMAGES_SOURCE_DIR, "categorized")

os.makedirs(CROP_IMAGES_SOURCE_DIR, exist_ok=True)
os.makedirs(CATEGORIZED_CROP_IMAGES_DIR, exist_ok=True)


def get_unique_filename(directory: str, original_filename: str) -> str:
    
    name, ext = os.path.splitext(original_filename)
    counter = 1
    new_filename = original_filename
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{name}_{counter}{ext}"
        counter += 1
    return new_filename



@app.get("/crop_images_for_validation/", response_model=List[CropImageMetadata])
async def get_crop_images_for_validation(
    limit: int = 15,
):
    all_image_filenames = [
        f for f in os.listdir(CROP_IMAGES_SOURCE_DIR)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')) and
           os.path.isfile(os.path.join(CROP_IMAGES_SOURCE_DIR, f))
    ]
    all_image_filenames.sort()

    num_available_images = len(all_image_filenames)
    
    random_batch_filenames = random.sample(
        all_image_filenames,
        min(limit, num_available_images)
    )

    image_metadata_list = [
        CropImageMetadata(image_path=f"/images/classify_skin_disease_crops_images/{filename}")
        for filename in random_batch_filenames
    ]

    return image_metadata_list


@app.post("/submit_crop_validations/", status_code=status.HTTP_201_CREATED)
async def submit_crop_validations(
    batch_data: BatchCropImageRatingRequest,
    db: Session = Depends(get_db)
):
    
    new_db_entries_count = 0
    errors = []

    
    


    for rating_data in batch_data.validations:
        try:
           
            new_entry = CropImageRating(
                image_path=rating_data.image_path,
                doctor_name=rating_data.doctor_name,
                comments=rating_data.comments,
                #crop_quality_rating=rating_data.crop_quality_rating,
                crop_diagnosis=rating_data.crop_diagnosis,
                confidence=rating_data.confidence,
                created_at=datetime.now(ZoneInfo("Europe/Rome"))
            )
            db.add(new_entry)
            new_db_entries_count += 1

            #relative_file_path_from_base_static = rating_data.image_path.replace("/images/", "", 1)
            #source_file_abs_path = os.path.join("images", relative_file_path_from_base_static)


        except Exception as e:
            db.rollback()
            errors.append(f"Unexpected error {rating_data.image_path}: {str(e)}")
            print(f"Error: Unexpected exception for {rating_data.image_path}: {str(e)}.")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        errors.append(f"Database commit failed: {str(e)}")
        print(f"Error: DB commit failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to commit data: {'; '.join(errors) if errors else 'Unknown error'}"
        )

    message = f"Successfully processed {new_db_entries_count} ratings."
    if errors:
        message += f" Some issues occurred: {', '.join(errors)}"
        raise HTTPException(
            status_code=status.HTTP_207_MULTI_STATUS,
            detail={"message": message, "errors": errors}
        )

    return {"message": message}


@app.get("/get_excel_data_categorized_doctor_skin_disease_crops_rating_batch/")
def get_categorized_excel_data(db: Session = Depends(get_db)):
    
    images = db.query(CropImageRating).all()
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No entries found in the doctor image validation table.")

    
    column_names = [column.name for column in CropImageRating.__table__.columns]
    data = []
    for image in images:
        row_data = {}
        for col_name in column_names:
            value = getattr(image, col_name)
            if isinstance(value, datetime):
                row_data[col_name] = value.isoformat()
            else:
                row_data[col_name] = value
        data.append(row_data)

    return JSONResponse(content=data)


from app.schemas import SingleCropImageMetadata, SingleCropQualityRatingRequest

STATIC_DIR = "images"


CROP_QUALITY_RATING_SOURCE_DIR = os.path.join(STATIC_DIR, "crop_quality_rating_images")
CROP_QUALITY_RATING_CHECKED_DIR = os.path.join(CROP_QUALITY_RATING_SOURCE_DIR, "checked")
CROP_IMAGES_SOURCE_DIR = os.path.join(STATIC_DIR, "classify_skin_disease_crops_images")
CATEGORIZED_CROP_IMAGES_DIR = os.path.join(CROP_IMAGES_SOURCE_DIR, "categorized")

os.makedirs(CROP_QUALITY_RATING_SOURCE_DIR, exist_ok=True)
os.makedirs(CROP_QUALITY_RATING_CHECKED_DIR, exist_ok=True)


@app.get("/get_next_crop_quality_rating_image/", response_model=Optional[SingleCropImageMetadata])
async def get_next_crop_quality_rating_image(db: Session = Depends(get_db)):
    
    all_image_filenames = [
        f for f in os.listdir(CROP_QUALITY_RATING_SOURCE_DIR)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')) and
           os.path.isfile(os.path.join(CROP_QUALITY_RATING_SOURCE_DIR, f))
    ]
    all_image_filenames.sort()

    
    #rated_image_urls = db.query(CropImageQualityRating.image_path).filter(
    #    CropImageQualityRating.image_path.like(f"/images/crop_quality_rating_images/%")
    #).all()
    #rated_image_urls_set = {url[0] for url in rated_image_urls}

    unrated_image_filenames = []
    for filename in all_image_filenames:
        #full_image_url_path = f"/images/crop_quality_rating_images/{filename}"
        #if full_image_url_path not in rated_image_urls_set:
        unrated_image_filenames.append(filename)

    if not unrated_image_filenames:
        return None 

    random_filename = random.choice(unrated_image_filenames)
    image_path_for_response = f"/images/crop_quality_rating_images/{random_filename}"

    return SingleCropImageMetadata(image_path=image_path_for_response)


@app.post("/submit_crop_quality_rating/", status_code=status.HTTP_201_CREATED)
async def submit_crop_quality_rating(
    rating_data: SingleCropQualityRatingRequest,
    db: Session = Depends(get_db)
):
    
    try:
        
        # existing_entry = db.query(CropImageQualityRating).filter(
        #     CropImageQualityRating.image_path == rating_data.image_path
        # ).first()

        # if existing_entry:
        #     raise HTTPException(
        #         status_code=status.HTTP_409_CONFLICT,
        #         detail=f"Image {rating_data.image_path} has already been rated."
        #     )

        
        new_entry = CropImageQualityRating(
            image_path=rating_data.image_path,
            doctor_name=rating_data.doctor_name,
            comments=rating_data.comments,
            crop_quality_rating=rating_data.crop_quality_rating,
            created_at=datetime.now(ZoneInfo("Europe/Rome")),

        )
        db.add(new_entry)
        db.commit() 
        db.refresh(new_entry)

        #relative_file_path_from_base_static = rating_data.image_path.replace("/images/", "", 1)
        #source_file_abs_path = os.path.join(STATIC_DIR, relative_file_path_from_base_static)
        
        return {"message": "Rating submitted!"}

    except Exception as e:
        db.rollback()
        print(f"Error processing {rating_data.image_path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error processing for {rating_data.image_path}: {str(e)}"
        )



@app.get("/get_excel_data_categorized_doctor_skin_disease_crops_rating_single_image/")
def get_categorized_excel_data(db: Session = Depends(get_db)):
    
    images = db.query(CropImageQualityRating).all()
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No entries found in the doctor image validation table.")

    
    column_names = [column.name for column in CropImageQualityRating.__table__.columns]
    data = []
    for image in images:
        row_data = {}
        for col_name in column_names:
            value = getattr(image, col_name)
            if isinstance(value, datetime):
                row_data[col_name] = value.isoformat()
            else:
                row_data[col_name] = value
        data.append(row_data)

    return JSONResponse(content=data)

@app.get("/get_image_subdirectories/", response_model=List[str])
async def get_image_subdirectories():
    
    subdirectories = []
    try:
        
        for entry in os.listdir(STATIC_DIR):
            full_path = os.path.join(STATIC_DIR, entry)
            
            if os.path.isdir(full_path) and not entry.startswith('.'):
                subdirectories.append(entry)
        subdirectories.sort() 
    except Exception as e:
        print(f"Error listing subdirectories: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve subdirectories.")
    return subdirectories




@app.post("/upload_images/")
async def upload_images(
    files: List[UploadFile] = File(...), 
    subdirectory: Optional[str] = Form(None) 
):
    
    uploaded_file_names = []
    
    
    if subdirectory:
        
        sanitized_subdirectory = Path(subdirectory).as_posix()
        if ".." in sanitized_subdirectory or sanitized_subdirectory.startswith("/"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subdirectory name.")
        
        target_directory = os.path.join(STATIC_DIR, sanitized_subdirectory)
    else:
        target_directory = STATIC_DIR

    
    os.makedirs(target_directory, exist_ok=True)

    for file in files:
        try:
            unique_filename = get_unique_filename(target_directory, file.filename)
            file_path = os.path.join(target_directory, unique_filename)

            with open(file_path, "wb") as buffer:
                while contents := await file.read(1024 * 1024): # Read 1MB chunks
                    buffer.write(contents)
            
            uploaded_file_names.append(unique_filename)
            print(f"Uploaded: {unique_filename} to {target_directory}")

        except Exception as e:
            print(f"Error uploading {file.filename}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload {file.filename}: {e}")
        finally:
            await file.close()

    return {"message": f"Successfully uploaded {len(uploaded_file_names)} files.", "uploaded_files": uploaded_file_names}



if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)  # Configure logging
    uvicorn.run(app, host="0.0.0.0", port=8000)

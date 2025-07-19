from fastapi import FastAPI, HTTPException, Depends, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.models import DoctorImageValidation, SessionLocal, engine, Base, Doctor
from app.schemas import DoctorImageValidationResponse, DoctorSchema, CropImageValidationResponse, CropImageValidationRequest  # Import DoctorSchema
import os
import shutil
import pandas as pd
import logging
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from typing import List, Tuple  # Import Tuple
from fastapi import FastAPI, HTTPException, Depends, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.models import SkinDiseaseImage, SessionLocal, engine, Base, CropImageValidation
from app.schemas import SkinDiseaseImageResponse, SkinDiseaseImageModel, SkinDiseaseImageResponse, PatientImageMetadata, \
    SkinToneClassificationResponse, SkinToneClassificationRequest # Create a new schema
from typing import Optional, List
import re
from app.schemas import DoctorImageValidationUpdateRequest
from fastapi.responses import FileResponse
from datetime import datetime
# No need to recreate tables here, model.py does it
# Base.metadata.create_all(bind=engine)
import random
from datetime import datetime, timezone # <--- Change UTC to timezone
from fastapi import status # <--- Add this line
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

origins = [
    "https://192.168.15.7:8000", # Your backend itself (often good to include)
    "http://localhost:8080",    # If you're serving HTML locally via http.server
    "http://127.0.0.1:8080",    # Alternative localhost
    "file://",                  # If opening HTML directly from your computer (common)
    "null",                     # Also if opening HTML directly from your computer (common fallback)
    "http://192.168.15.7:8080", # If your server serves the frontend HTML on this port
    "https://192.168.15.7",     # If your server serves frontend HTML on standard HTTPS port
    "*",                         # FOR DEVELOPMENT ONLY: Allows all origins. Use with CAUTION.
    "https://medicalimages.apice.unibo.it"                            # If using '*', you generally shouldn't allow credentials.
                                # It's best to be specific.
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development, specify origins in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.mount("/images", StaticFiles(directory="images"), name="images")
# Mount your static files at a path, e.g., /static-frontend
# Make sure the directory path is correct on your VM
# IMPORTANT: Ensure your 'main.html' and other frontend files are actually
# inside a 'frontend' sub-directory within this specified path.
app.mount("/frontend", StaticFiles(directory="/root/Unibo_Doctor_App/Unibo_Doctors_Application-main (1) (2)/Unibo_Doctors_Application-main/frontend"), name="static_frontend")

# Optional: Redirect root to your main HTML file
@app.get("/")
async def root():
    return RedirectResponse(url="/static-frontend/main.html")

# (Your /get_skin_disease_data/ endpoint would remain as is)




# --- Serve skin disease images from the external hard drive at a NEW prefix ---
skin_disease_data_path = "/root/test_data" #"/media/verbose193/E0909AEF909ACB82/Thesis Working Directory/Skin disesases data"
app.mount("/skin_disease_data", StaticFiles(directory=skin_disease_data_path), name="skin_disease_data")

skin_disease_crop_data_path = "/root/test_data" #"/media/verbose193/E0909AEF909ACB82/Thesis Working Directory/Skin disesases data"
app.mount("/skin_disease_data2", StaticFiles(directory=skin_disease_crop_data_path), name="skin_disease_data2")


def find_image_pair(directory="images") -> List[Tuple[str, str]]:
    """
    Finds pairs of original and mask images in the given directory.
    Assumes that original images and mask images have the same base name,
    and mask images have '_mask' appended before the extension.

    For example:
    original image:  'image1.jpg'
    mask image:      'image1_mask.jpg'

    Returns:
        A list of tuples, where each tuple contains the original image filename
        and the corresponding mask image filename.
        Returns an empty list if no pairs are found.
    """
    image_pairs = []
    try:
        for filename in os.listdir(directory):
            if "_mask" not in filename:  # Process only original images
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
    """
    Retrieves the first uncategorized image pair.
    """
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
            disease_name="Unknown",  # Changed from None to "Unknown"
            category=None
        )
    raise HTTPException(status_code=404, detail="No image pairs to categorize found.")


@app.get("/categorize_image/{current_displayed_filename}", response_model=Optional[DoctorImageValidationResponse])
async def get_next_uncategorized_image(current_displayed_filename: str):
    """
    Retrieves the next uncategorized image pair after the given filename.
    """
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
    current_filename: str = Form(...),  # Base filename (without _mask)
    doctor_name: str = Form(...),
    #years_of_experience: int = Form(...),  # Feature 1
    rating: int = Form(...),
    comments: Optional[str] = Form(None),
    mask_comments: Optional[str] = Form(None),
    disease_name: str = Form(...),
    category: str = Form(...),
    real_generated: str = Form(...),  # Feature 2
    realism_rating: Optional[int] = Form(None),  # Feature 2
    image_precision: str = Form(...),  # Feature 2
    skin_color_precision: Optional[int] = Form(None),  # Feature 2
    confidence_level: Optional[int] = Form(None),  # Feature 2
    crop_quality_rating: Optional[int] = Form(None),  # Feature 3
    crop_diagnosis: str = Form(...),  # Feature 3
    fitzpatrick_scale: Optional[str] = Form(None),  # Feature 4
    db: Session = Depends(get_db),
):
    """
    Saves the categorization details to the database and moves the image files.
    """
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
        """
        Moves a file, handling potential filename collisions.
        """
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

        # Update the additional fields
        #db_image.years_of_experience = years_of_experience
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
    """
    Retrieves images for a specific disease.
    """
    images = db.query(DoctorImageValidation).filter(
        DoctorImageValidation.disease_name == disease_name
    ).all()
    return images


@app.post("/update_image_details/{image_id}")
async def update_image_details(
    image_id: int, # Changed from Form to int
    doctor_name: str = Form(...),
    #years_of_experience: int = Form(...),  # Feature 1
    rating: int = Form(...),
    comments: Optional[str] = Form(None),
    mask_comments: Optional[str] = Form(None),
    disease_name: str = Form(...),
    category: str = Form(...),
    real_generated: str = Form(...),  # Feature 2
    realism_rating: Optional[int] = Form(None),  # Feature 2
    image_precision: str = Form(...),  # Feature 2
    skin_color_precision: Optional[int] = Form(None),  # Feature 2
    confidence_level: Optional[int] = Form(None),  # Feature 2
    crop_quality_rating: Optional[int] = Form(None),  # Feature 3
    crop_diagnosis: str = Form(...),  # Feature 3
    fitzpatrick_scale: Optional[str] = Form(None),  # Feature 4
    db: Session = Depends(get_db),
):
    """
    Updates the details of an image in the database and moves the image files
    if the category has changed.
    """
    db_image = db.query(DoctorImageValidation).filter(DoctorImageValidation.id == image_id).first()
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")

    old_category = db_image.category  # Store the old category
    old_image_path = db_image.image_path
    old_mask_path = db_image.mask_path

    # Update the database record
    db_image.doctor_name = doctor_name
    #db_image.years_of_experience = years_of_experience # Feature 1
    db_image.rating = rating
    db_image.comments = comments
    db_image.mask_comments = mask_comments
    db_image.disease_name = disease_name
    db_image.category = category
    db_image.real_generated = real_generated # Feature 2
    db_image.realism_rating = realism_rating # Feature 2
    db_image.image_precision = image_precision # Feature 2
    db_image.skin_color_precision = skin_color_precision # Feature 2
    db_image.confidence_level = confidence_level # Feature 2
    db_image.crop_quality_rating = crop_quality_rating # Feature 3
    db_image.crop_diagnosis = crop_diagnosis # Feature 3
    db_image.fitzpatrick_scale = fitzpatrick_scale # Feature 4
    db.commit()  # Commit the changes *before* moving files

    # Move files if the category has changed
    if old_category != category:
        try:
            # Define source and destination directories
            source_original_path = os.path.join(old_image_path)
            source_mask_path = os.path.join(old_mask_path)
            destination_dir = os.path.join("images", category)  # Correct destination
            os.makedirs(destination_dir, exist_ok=True)
            destination_original_path = os.path.join(destination_dir, os.path.basename(old_image_path))
            destination_mask_path = os.path.join(destination_dir, os.path.basename(old_mask_path))

            def move_file_with_collision_handling(source, destination):
                """
                Moves a file, handling filename collisions.
                """
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

            # Update the database with the new paths
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
    """
    Downloads all categorization entries from the database as an Excel file.
    """
    categorizations = db.query(DoctorImageValidation).all()
    if not categorizations:
        raise HTTPException(
            status_code=404, detail="No categorizations found in the database."
        )

    # Convert the database entries to a list of dictionaries
    data = [entry.__dict__ for entry in categorizations]
    # Remove the SQLAlchemy internal attributes
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
    """
    Filters categorization entries by category and optionally by disease name.
    Returns a list of DoctorImageValidationResponse objects.
    """
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
    """
    Retrieves all categorization entries from the database.
    """
    return db.query(DoctorImageValidation).all()


@app.get("/disease_names/", response_model=List[str])
async def get_disease_names(db: Session = Depends(get_db)):
    """
    Retrieves all distinct disease names from the database.
    """
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


@app.get("/doctors/", response_model=List[DoctorSchema])
async def get_doctors(db: Session = Depends(get_db)):
    """
    Retrieves all doctors from the database.
    """
    doctors = db.query(Doctor).all()
    return doctors

@app.delete("/doctors/")
async def delete_doctors_table(db: Session = Depends(get_db)):
    """
    Deletes the doctors table from the database.
    """
    inspector = inspect(db.bind)
    if not inspector.has_table("doctors"):
        raise HTTPException(status_code=404, detail="Doctors table not found")

    # Use a raw SQL query to delete the table
    try:
        db.execute(text("DROP TABLE doctors"))
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete table: {e}")

    return {"message": "Doctors table deleted successfully"}


def drop_table(db: Session, table_name: str):
    """
    Drops the specified table from the database.

    Args:
        db: The database session.
        table_name: The name of the table to drop.
    """
    try:
        if table_name == 'doctor_image_validation':
            DoctorImageValidation.__table__.drop(bind=engine)
        elif table_name == 'doctors':
            Doctor.__table__.drop(bind=engine)
        else:
            raise HTTPException(status_code=400, detail=f"Table '{table_name}' not found.")
        db.commit()  # Commit the changes after dropping the table
        logging.info(f"Table '{table_name}' dropped successfully.")
    except OperationalError as e:
        logging.error(f"Error dropping table '{table_name}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to drop table '{table_name}': {e}"
        )
    except Exception as e:
        logging.error(f"Unexpected error dropping table '{table_name}': {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


from sqlalchemy import text
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
# ... other imports from your code

@app.delete("/delete_table/{table_name}")
def delete_table_route(table_name: str, db: Session = Depends(get_db)):
    """
    Deletes the specified table.

    Args:
        table_name: The name of the table to delete ('doctor_image_validation', 'doctors', or 'skin_disease_image').
        db: The database session.

    Returns:
        A dictionary indicating the result of the operation.
    """
    if table_name not in ('doctor_image_validation', 'doctors', 'skin_disease_image', 'crop_image_validation', 'crop_image_quality_rating'\
                          'crop_image_rating'):
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
    """
    Populates the database with image paths relative to image_root, and links masks, in a single pass.
    Skips files with '_crop' in the filename.
    """
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
                            # Handle mask
                            match = re.match(r"(.+)_mask\.png$", filename)
                            if not match:
                                print(f"Invalid mask filename: {filename}")
                                continue

                            base_image_name = match.group(1) + ".png"
                            print(f"Processing mask: {filename}, base_image_name: {base_image_name}")

                            # Query for matching image
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
                            # Handle base image
                            new_image = SkinDiseaseImage(
                                disease_name_amended=amended_dir,
                                disease_name=disease_dir,
                                persona_digits=persona_digits,
                                example_digit=example_digit,
                                image_name=filename,
                                image_path=os.path.join("/skin_disease_data", relative_path)
                            )
                            # Check for corresponding mask file
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


# --- Routes for viewing and editing image details ---
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


# # --- Routes for skin tone classification ---
# @app.get("/patient_images/{persona_digits}", response_model=List[SkinDiseaseImageResponse])
# async def get_patient_images_for_classification(persona_digits: str, db: Session = Depends(get_db)):
#     images = db.query(SkinDiseaseImage).filter(SkinDiseaseImage.persona_digits == persona_digits).all()
#     if not images:
#         raise HTTPException(status_code=404, detail=f"No images found for patient {persona_digits}")
#     return images

# @app.post("/classify_skin_tone/{persona_digits}")
# async def classify_skin_tone(persona_digits: str, fitzpatrick_scale: str = Form(...), db: Session = Depends(get_db)):
#     images = db.query(SkinDiseaseImage).filter(SkinDiseaseImage.persona_digits == persona_digits).all()
#     if not images:
#         raise HTTPException(status_code=404, detail=f"No images found for patient {persona_digits}")
#     for image in images:
#         image.fitzpatrick_scale = fitzpatrick_scale
#     db.commit()
#     return {"message": f"Skin tone for patient {persona_digits} classified as {fitzpatrick_scale}."}

# --- (Optional) Route to get unique persona digits for classification UI ---
# @app.get("/unique_patients/", response_model=List[str])
# async def get_unique_patients(db: Session = Depends(get_db)):
#     unique_personas = db.query(SkinDiseaseImage.persona_digits).distinct().all()
#     return [persona[0] for persona in unique_personas if persona[0] is not None]

# from app.schemas import PatientImageMetadata

# # --- NEW ROUTE: Get Images for a Specific Patient ID ---
# @app.get("/patient_images/{persona_digits}", response_model=List[PatientImageMetadata])
# async def get_patient_images(persona_digits: str, db: Session = Depends(get_db)): # Added db dependency
#     """
#     Retrieves all image and mask paths for a given patient ID (persona_digits) from the database.
#     """
#     # Query SkinDiseaseImage table for all images associated with this persona_digits
#     images_from_db = db.query(SkinDiseaseImage).filter(
#         SkinDiseaseImage.persona_digits == persona_digits
#     ).all()

#     if not images_from_db:
#         raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="No images found for this patient in the database.")

#     images_data = []
#     for img_entry in images_from_db:
#         images_data.append(PatientImageMetadata(
#             image_path=img_entry.image_path, # Assuming this is a full URL path like /images/... or /skin_disease_data/...
#             image_name=img_entry.image_name,
#             mask_path=img_entry.mask_path,
#             mask_name=img_entry.mask_name
#         ))
    
#     # Sort the images for consistent display, e.g., by image_name
#     images_data.sort(key=lambda x: x.image_name) 
    
#     return images_data


# --- UPDATED ROUTE: Get Unique Patient IDs for Skin Tone Classification (with validation filter) ---
@app.get("/unique_patients/", response_model=List[str])
async def get_unique_patients(
    validation_status: Optional[str] = Query("all", description="Filter by validation status: 'all', 'validated', 'unvalidated'"),
    db: Session = Depends(get_db)
):
    """
    Retrieves unique patient (persona) IDs from the SkinDiseaseImage table,
    optionally filtered by validation status (doctor_name presence).
    """
    query = db.query(SkinDiseaseImage.persona_digits)

    if validation_status == "validated":
        # Filter for entries where doctor_name is not NULL and not an empty string
        query = query.filter(SkinDiseaseImage.doctor_name.isnot(None), SkinDiseaseImage.doctor_name != '')
    elif validation_status == "unvalidated":
        # Filter for entries where doctor_name is NULL or an empty string
        query = query.filter(or_(SkinDiseaseImage.doctor_name.is_(None), SkinDiseaseImage.doctor_name == ''))
    # If validation_status is 'all' or any other value, no filter is applied

    unique_personas = query.distinct().all()
    # Extract the string from the tuple and filter out any None values
    return sorted([persona[0] for persona in unique_personas if persona[0] is not None])
from sqlalchemy.sql import or_

# --- UPDATED ROUTE: Get Images for a Specific Patient ID (with validation filter) ---
@app.get("/patient_images/{persona_digits}", response_model=List[PatientImageMetadata])
async def get_patient_images(
    persona_digits: str,
    validation_status: Optional[str] = Query("all", description="Filter by validation status: 'all', 'validated', 'unvalidated'"),
    db: Session = Depends(get_db)
):
    """
    Retrieves all image and mask paths for a given patient ID (persona_digits) from the database,
    optionally filtered by validation status.
    """
    query = db.query(SkinDiseaseImage).filter(
        SkinDiseaseImage.persona_digits == persona_digits
    )

    if validation_status == "validated":
        query = query.filter(SkinDiseaseImage.doctor_name.isnot(None), SkinDiseaseImage.doctor_name != '')
    elif validation_status == "unvalidated":
        query = query.filter(or_(SkinDiseaseImage.doctor_name.is_(None), SkinDiseaseImage.doctor_name == ''))
    
    images_from_db = query.all()

    if not images_from_db:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="No images found for this patient with the specified validation status in the database.")

    images_data = []
    for img_entry in images_from_db:
        images_data.append(PatientImageMetadata(
            image_path=img_entry.image_path,
            image_name=img_entry.image_name,
            mask_path=img_entry.mask_path,
            mask_name=img_entry.mask_name
        ))
    
    images_data.sort(key=lambda x: x.image_name) 
    
    return images_data



from app.schemas import SkinToneClassificationRequest, SkinToneClassificationResponse
from http import HTTPStatus

# --- UPDATED ROUTE: Classify Skin Tone (Implements Conditional SkinDiseaseImage Update/Create) ---
# @app.post("/classify_skin_tone/{persona_digits}", response_model=SkinToneClassificationResponse, status_code=HTTPStatus.CREATED)
# async def classify_skin_tone(
#     persona_digits: str,
#     classification_data: SkinToneClassificationRequest, # Expecting JSON body from frontend
#     db: Session = Depends(get_db)
# ):
#     """
#     Classifies the skin tone for a given patient (persona_digits) by a specific doctor.
#     - Always creates a new entry in SkinToneClassification (logging each classification event).
#     - Conditionally updates or creates entries in SkinDiseaseImage based on existing doctor_name.
#     - No image directory is moved.
#     """
#     try:
#         # Fetch the first SkinDiseaseImage entry for this persona_digits to get image/mask/crop paths
#         # This assumes that if a patient has multiple images, picking the first one is acceptable
#         # for logging in SkinToneClassification.
#         # first_image_entry = db.query(models.SkinDiseaseImage).filter(
#         #     models.SkinDiseaseImage.persona_digits == persona_digits
#         # ).first()

#         # image_name_log = None
#         # image_path_log = None
#         # mask_name_log = None
#         # mask_path_log = None
#         # crop_image_name_log = None
#         # crop_image_path_log = None
#         # crop_mask_name_log = None
#         # crop_mask_path_log = None

#         # if first_image_entry:
#         #     image_name_log = first_image_entry.image_name
#         #     image_path_log = first_image_entry.image_path
#         #     mask_name_log = first_image_entry.mask_name
#         #     mask_path_log = first_image_entry.mask_path
#         #     crop_image_name_log = first_image_entry.crop_image_name
#         #     crop_image_path_log = first_image_entry.crop_image_path
#         #     crop_mask_name_log = first_image_entry.crop_mask_name
#         #     crop_mask_path_log = first_image_entry.crop_mask_path
#         # else:
#         #     print(f"Warning: No SkinDiseaseImage entry found for persona_digits {persona_digits}. "
#         #           "Image/mask/crop paths in SkinToneClassification will be null.")


#         # # 1. Always create a new entry in SkinToneClassification
#         # new_classification = models.SkinToneClassification(
#         #     persona_digits=persona_digits,
#         #     doctor_name=classification_data.doctor_name,
#         #     fitzpatrick_scale=classification_data.fitzpatrick_scale,
#         #     image_name=image_name_log, # Populating new fields
#         #     image_path=image_path_log,
#         #     mask_name=mask_name_log,
#         #     mask_path=mask_path_log,
#         #     crop_image_name=crop_image_name_log,
#         #     crop_image_path=crop_image_path_log,
#         #     crop_mask_name=crop_mask_name_log,
#         #     crop_mask_path=crop_mask_path_log
#         # )
#         # db.add(new_classification)
#         message_part_1 = f"New classification recorded for patient {persona_digits} by doctor {classification_data.doctor_name}."

#         # 2. Conditionally update or create entries in SkinDiseaseImage
#         skin_disease_images = db.query(SkinDiseaseImage).filter(
#             SkinDiseaseImage.persona_digits == persona_digits
#         ).all()

#         # if not skin_disease_images:
#         #     print(f"Warning: No SkinDiseaseImage entries found for persona_digits {persona_digits}. "
#         #           "No SkinDiseaseImage records to update/create.")
#         #     db.commit() # Commit the SkinToneClassification log entry
#         #     return {"message": f"{message_part_1} No associated image records found to update/create."}

#         for image_entry in skin_disease_images:
#             # Check if doctor_name field is NULL or empty
#             if image_entry.doctor_name is None or image_entry.doctor_name == "":
#                 # Condition 1: Doctor name is not set, so UPDATE the existing entry
#                 image_entry.doctor_name = classification_data.doctor_name
#                 image_entry.fitzpatrick_scale = classification_data.fitzpatrick_scale
#                 # SQLAlchemy automatically tracks changes to managed objects for updates
#                 print(f"Updated existing SkinDiseaseImage ID {image_entry.id} for {image_entry.image_name}")
#             else:
#                 # Condition 2: Doctor name is already set, so CREATE a new entry
#                 new_skin_disease_image_entry = SkinDiseaseImage(
#                     disease_name_amended=image_entry.disease_name_amended,
#                     disease_name=image_entry.disease_name,
#                     persona_digits=image_entry.persona_digits,
#                     example_digit=image_entry.example_digit,
#                     image_name=image_entry.image_name, # Same image name
#                     mask_name=image_entry.mask_name,
#                     image_path=image_entry.image_path, # Same image path
#                     mask_path=image_entry.mask_path,
#                     crop_image_name=image_entry.crop_image_name,
#                     crop_image_path=image_entry.crop_image_path,
#                     crop_mask_name=image_entry.crop_mask_name,
#                     crop_mask_path=image_entry.crop_mask_path,
                    
#                     doctor_name=classification_data.doctor_name, # New doctor name
#                     fitzpatrick_scale=classification_data.fitzpatrick_scale, # New fitzpatrick scale
#                     # Other fields can be copied or left as default/null if not relevant to classification
#                     rating=image_entry.rating,
#                     comments=image_entry.comments,
#                     category=image_entry.category,
#                     years_of_experience=image_entry.years_of_experience,
#                     real_generated=image_entry.real_generated,
#                     realism_rating=image_entry.realism_rating,
#                     image_precision=image_entry.image_precision,
#                     skin_color_precision=image_entry.skin_color_precision,
#                     confidence_level=image_entry.confidence_level,
#                     crop_quality_rating=image_entry.crop_quality_rating,
#                     crop_diagnosis=image_entry.crop_diagnosis,
#                     created_at=datetime.now() # Set new creation timestamp
#                 )
#                 db.add(new_skin_disease_image_entry)
#                 print(f"Created new SkinDiseaseImage entry for {image_entry.image_name} with ID {new_skin_disease_image_entry.id}")

#         db.commit() # Commit all changes (SkinToneClassification log and SkinDiseaseImage updates/creations)

#         return {"message": f"{message_part_1} Associated image records conditionally updated/created."}

#     except Exception as e:
#         db.rollback()
#         print(f"Error classifying skin tone for {persona_digits}: {e}")
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail=f"An unexpected error occurred during classification: {e}"
#         )
    
# --- UPDATED ROUTE: Classify Skin Tone (Implements Conditional SkinDiseaseImage Update/Create) ---
@app.post("/classify_skin_tone/{persona_digits}", response_model=SkinToneClassificationResponse, status_code=HTTPStatus.CREATED)
async def classify_skin_tone(
    persona_digits: str,
    classification_data: SkinToneClassificationRequest, # Expecting JSON body from frontend
    db: Session = Depends(get_db)
):
    """
    Classifies the skin tone for a given patient (persona_digits) by a specific doctor.
    - Always creates a new entry in SkinToneClassification (logging each classification event).
    - Conditionally updates or creates entries in SkinDiseaseImage based on existing doctor_name.
    - No image directory is moved.
    """
    try:
        # The frontend sends doctor_name and fitzpatrick_scale.
        # We will apply this classification to all images for the given persona_digits
        # that are currently 'unvalidated' (doctor_name is NULL or empty).
        # If an image for this persona_digits already has a doctor_name, a new entry will be created.

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

        for image_entry in skin_disease_images:
            # Determine image/mask/crop paths for the SkinToneClassification log entry
            image_name_log = image_entry.image_name
            image_path_log = image_entry.image_path
            mask_name_log = image_entry.mask_name
            mask_path_log = image_entry.mask_path
            crop_image_name_log = image_entry.crop_image_name
            crop_image_path_log = image_entry.crop_image_path
            crop_mask_name_log = image_entry.crop_mask_name
            crop_mask_path_log = image_entry.crop_mask_path

            # Always create a new entry in SkinToneClassification (logging each classification event)
            new_classification_log = models.SkinToneClassification(
                persona_digits=persona_digits,
                doctor_name=classification_data.doctor_name,
                fitzpatrick_scale=classification_data.fitzpatrick_scale,
                image_name=image_name_log,
                image_path=image_path_log,
                mask_name=mask_name_log,
                mask_path=mask_path_log,
                crop_image_name=crop_image_name_log,
                crop_image_path=crop_image_path_log,
                crop_mask_name=crop_mask_name_log,
                crop_mask_path=crop_mask_path_log
            )
            db.add(new_classification_log)

            # Conditionally update or create entries in SkinDiseaseImage
            if image_entry.doctor_name is None or image_entry.doctor_name == "":
                # Condition 1: Doctor name is not set, so UPDATE the existing entry
                image_entry.doctor_name = classification_data.doctor_name
                image_entry.fitzpatrick_scale = classification_data.fitzpatrick_scale
                updated_count += 1
                print(f"Updated existing SkinDiseaseImage ID {image_entry.id} for {image_entry.image_name}")
            else:
                # Condition 2: Doctor name is already set, so CREATE a new entry
                # This ensures a history of classifications by different doctors or re-classifications
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
                    
                    rating=image_entry.rating,
                    comments=image_entry.comments,
                    category=image_entry.category,
                    years_of_experience=image_entry.years_of_experience,
                    real_generated=image_entry.real_generated,
                    realism_rating=image_entry.realism_rating,
                    image_precision=image_entry.image_precision,
                    skin_color_precision=image_entry.skin_color_precision,
                    confidence_level=image_entry.confidence_level,
                    crop_quality_rating=image_entry.crop_quality_rating,
                    crop_diagnosis=image_entry.crop_diagnosis,
                    created_at=datetime.now()
                )
                db.add(new_skin_disease_image_entry)
                created_count += 1
                print(f"Created new SkinDiseaseImage entry for {image_entry.image_name} with ID {new_skin_disease_image_entry.id}")

        db.commit()

        return {"message": f"Classification submitted for patient {persona_digits}. {updated_count} existing records updated, {created_count} new records created."}

    except Exception as e:
        db.rollback()
        print(f"Error classifying skin tone for {persona_digits}: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during classification: {e}"
        )

@app.get("/check_skin_disease_images/", response_model=List[SkinDiseaseImageResponse])
async def get_skin_disease_image_contents(db: Session = Depends(get_db)):
    """
    Retrieves and returns all entries from the skin_disease_image table.
    """
    contents = db.query(SkinDiseaseImage).all()
    return contents

@app.get("/download_skin_disease_excel/")
async def download_skin_disease_excel(db: Session = Depends(get_db)):
    """
    Downloads all skin disease image entries from the database as an Excel file.
    """
    images = db.query(SkinDiseaseImage).all()
    if not images:
        raise HTTPException(status_code=404, detail="No entries found in the skin disease table.")

    # Use only defined column names
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

    # Use only defined column names
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
    """
    Update crop image and mask info in SkinDiseaseImage table.
    Only updates fields if filename contains '_crop'.

    Matches by:
      - disease_name_amended
      - disease_name
      - persona_digits
      - example_digit
      - image_name (base image, not the crop one)
    """
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


                    # Assumes original image is same as crop name minus "_crop"
                    for filename in os.listdir(example_path):
                        if not (filename.endswith(".png") or filename.endswith(".jpg")):
                            continue

                        if "_crop" not in filename:
                            continue

                        is_mask = "_mask" in filename
                        relative_path = os.path.join(amended_dir, disease_dir, persona_dir, example_dir, filename)

                        # Try to infer base image name (original image this crop is derived from)
                        # E.g., if filename is "abc_crop.png", base is "abc.png"
                        base_image_name = filename.replace("_crop", "").replace("_mask", "")

                        # Query matching DB entry (specific image)
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

# import os
# import shutil
# from fastapi import HTTPException

# IMAGE_ROOT = "images"  # root images folder
# DISEASE_FOLDER = os.path.join(IMAGE_ROOT, "disease")
# NON_DISEASE_FOLDER = os.path.join(IMAGE_ROOT, "non-disease")

# def get_unique_filename(dir_path: str, filename: str) -> str:
#     """
#     If filename exists in dir_path, append suffix _1, _2, etc. until unique.
#     """
#     base, ext = os.path.splitext(filename)
#     candidate = filename
#     count = 1
#     while os.path.exists(os.path.join(dir_path, candidate)):
#         candidate = f"{base}_{count}{ext}"
#         count += 1
#     return candidate

# @app.post("/skin_disease_image/update/{image_name}", response_model=SkinDiseaseImageResponse)
# def update_skin_disease_image_post(
#     image_name: str,
#     payload: DoctorImageValidationUpdateRequest,
#     db: Session = Depends(get_db)
# ):
#     db_record = db.query(SkinDiseaseImage).filter(SkinDiseaseImage.image_name == image_name).first()
#     if not db_record:
#         raise HTTPException(status_code=404, detail="Image record not found")

#     update_data = payload.dict(exclude_unset=True)  # update only fields sent

#     # Update DB fields first
#     for key, value in update_data.items():
#         setattr(db_record, key, value)

#     # Decide target folder based on category
#     category = update_data.get("category")
#     if category not in ("disease", "non-disease"):
#         raise HTTPException(status_code=400, detail="Category must be 'disease' or 'non-disease'")

#     target_folder = DISEASE_FOLDER if category == "disease" else NON_DISEASE_FOLDER

#     # Ensure target folder exists
#     os.makedirs(target_folder, exist_ok=True)

#     # Prepare old image filenames and their current paths
#     # Use image_name as base for constructing others
#     base_name, ext = os.path.splitext(image_name)
#     old_paths = {
#         "image_path": os.path.join(IMAGE_ROOT, db_record.image_path) if db_record.image_path else None,
#         "mask_path": os.path.join(IMAGE_ROOT, db_record.mask_path) if db_record.mask_path else None,
#         "crop_image_path": os.path.join(IMAGE_ROOT, db_record.crop_image_path) if db_record.crop_image_path else None,
#         "crop_mask_path": os.path.join(IMAGE_ROOT, db_record.crop_mask_path) if db_record.crop_mask_path else None,
#     }

#     # New file names dictionary
#     new_filenames = {}

#     # Define expected suffixes for each image type
#     suffix_map = {
#         "image_path": "",  # original
#         "mask_path": "_mask",
#         "crop_image_path": "_crop",
#         "crop_mask_path": "_crop_mask",
#     }

#     # Move and rename files if they exist
#     for field, old_full_path in old_paths.items():
#         if old_full_path and os.path.isfile(old_full_path):
#             orig_filename = os.path.basename(old_full_path)
#             # Compose new filename, ensure unique in target folder
#             base_file_name = base_name + suffix_map[field] + ext
#             unique_filename = get_unique_filename(target_folder, base_file_name)

#             # Move file
#             new_full_path = os.path.join(target_folder, unique_filename)
#             shutil.move(old_full_path, new_full_path)

#             # Save relative path in DB (relative to IMAGE_ROOT)
#             relative_path = os.path.relpath(new_full_path, IMAGE_ROOT)
#             new_filenames[field] = relative_path.replace("\\", "/")  # for Windows compatibility

#         else:
#             new_filenames[field] = getattr(db_record, field)  # no change if file missing

#     # Update DB paths with new relative paths
#     for key, val in new_filenames.items():
#         setattr(db_record, key, val)

#     db.commit()
#     db.refresh(db_record)

#     return db_record

import os
import shutil
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models import DoctorImageValidation
from app.schemas import DoctorImageValidationRequest, DoctorImageValidationResponse, CropImageValidationResponse, CropImageValidationRequest
#from database import get_db

router = APIRouter()

BASE_IMAGE_DIR = "images"
DISEASE_DIR = os.path.join(BASE_IMAGE_DIR, "disease")
NON_DISEASE_DIR = os.path.join(BASE_IMAGE_DIR, "non-disease")



def move_and_rename_file(src_path: str, dest_dir: str) -> str:
    """
    Moves a file to destination directory, adds suffix if filename exists,
    returns new filename.
    """
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
    return os.path.basename(dest_path)  # Return new filename only


import os
import shutil

def move_with_unique_name(src_path: str, target_dir: str):
    src_path = os.path.abspath(src_path)  # Ensure it's absolute

    if not os.path.exists(src_path):
        print(f"DEBUG: Source file not found for moving: {src_path}") # Added debug print
        return None, None # Return None if source file doesn't exist
    
    os.makedirs(target_dir, exist_ok=True)

    base_name = os.path.basename(src_path)
    name, ext = os.path.splitext(base_name)
    dest_path = os.path.join(target_dir, base_name)
    counter = 1

    # Loop to find a unique name
    while os.path.exists(dest_path):
        new_name = f"{name}_{counter}{ext}"
        dest_path = os.path.join(target_dir, new_name)
        counter += 1

    shutil.move(src_path, dest_path)
    
    # Return the new filename (basename) and the absolute path
    return os.path.basename(dest_path), dest_path


@app.post("/skin_disease_image/update/{base_name}", response_model=DoctorImageValidationResponse)
def submit_validation(
    base_name: str, # This is the original base name from the frontend (e.g., "image1")
    payload: DoctorImageValidationRequest,
    db: Session = Depends(get_db)
):
    print(payload)
    # Define the single target directory for all categorized images
    CATEGORIZED_IMAGES_DIR = os.path.join(BASE_IMAGE_DIR, "categorized_images_crops_categorized")

    # Define the source paths for the images based on BASE_IMAGE_DIR and the original base_name
    # Assuming original images are directly in BASE_IMAGE_DIR
    #orig_image_src = os.path.join(BASE_IMAGE_DIR, f"categorized_images/{base_name}.jpg")
    #orig_mask_src = os.path.join(BASE_IMAGE_DIR, f"categorized_images/{base_name}_mask.jpg")
    crop_image_src = os.path.join(BASE_IMAGE_DIR, f"categorized_images/{base_name}_crop.jpg")
    crop_mask_src = os.path.join(BASE_IMAGE_DIR, f"categorized_images/{base_name}_crop_mask.jpg")

    # Move images and get their new unique filenames and absolute paths
    #image_new_filename, image_abs_path = move_with_unique_name(orig_image_src, CATEGORIZED_IMAGES_DIR)
    #mask_new_filename, mask_abs_path = move_with_unique_name(orig_mask_src, CATEGORIZED_IMAGES_DIR)
    crop_new_filename, crop_abs_path = move_with_unique_name(crop_image_src, CATEGORIZED_IMAGES_DIR)
    crop_mask_new_filename, crop_mask_abs_path = move_with_unique_name(crop_mask_src, CATEGORIZED_IMAGES_DIR)

    # Check if any required image failed to move
    # If a source file was not found, move_with_unique_name returns (None, None)
    #if not image_new_filename: # Original image is mandatory
    #    raise HTTPException(status_code=400, detail=f"Original image file not found or could not be moved: {orig_image_src}")

    # Construct the URL paths to be stored in the database
    # These paths are relative to the `/images/` FastAPI mount point
    #image_db_path = f"/images/categorized_images_crops_categorized/{image_new_filename}"
    #mask_db_path = f"/images/categorized_images_crops_categorized/{mask_new_filename}" if mask_new_filename else None
    crop_db_path = f"/images/categorized_images_crops_categorized/{crop_new_filename}" if crop_new_filename else None
    crop_mask_db_path = f"/images/categorized_images_crops_categorized/{crop_mask_new_filename}" if crop_mask_new_filename else None

    # Save to DB
    db_record = DoctorImageValidation(
        image_path=None,#image_db_path,
        mask_path=None,#mask_db_path,
        crop_path=crop_db_path,
        crop_mask_path=crop_mask_db_path,
        doctor_name=payload.doctor_name, #--------------DONE
        mask_rating=payload.mask_rating,   #--------------DONE
        comments=payload.comments,   #--------------DONE
        mask_comments=payload.mask_comments,   #--------------DONE
        disease_name=None,#payload.disease_name,
        category=None,#payload.category,
        real_generated=payload.real_generated,   #--------------DONE
        realism_rating=payload.realism_rating,   #--------------DONE
        image_precision=payload.image_precision,   #--------------DONE
        skin_color_precision=None,#payload.skin_color_precision,
        confidence_level=payload.confidence_level,   #--------------DONE
        crop_quality_rating=None,#payload.crop_quality_rating,
        crop_diagnosis=None,#payload.crop_diagnosis,
        fitzpatrick_scale=None,#payload.fitzpatrick_scale,
        created_at=datetime.utcnow()
    )

    print(payload)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    return db_record

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


import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

IMAGE_DIR = "/images/categorized_images"  # path to your images folder

STATIC_DIR = "images"
IMAGE_NAMES_DIR = os.path.join(STATIC_DIR, "categorized_images")
os.makedirs(IMAGE_NAMES_DIR, exist_ok=True) # Ensure the new directory exists


from fastapi.responses import JSONResponse
import os

from fastapi.responses import JSONResponse
import os

@app.get("/get_all_base_names")
async def get_all_base_names():
    try:
        files = os.listdir(IMAGE_NAMES_DIR)
        files_set = set(files)

        valid_bases = set()

        for f in files:
            if f.endswith("_crop.jpg"):
                base = f.replace("_crop.jpg", "")
                crop_mask = f"{base}_crop_mask.jpg"
                if crop_mask in files_set:
                    valid_bases.add(base)

        return JSONResponse(content=sorted(valid_bases))

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)



# @app.get("/get_all_base_names")
# async def get_all_base_names():
#     try:
#         files = os.listdir(IMAGE_NAMES_DIR)
#         # Collect all filenames without extensions for jpg and png separately
#         jpg_files = set(f for f in files if f.endswith(".jpg"))
#         png_files = set(f for f in files if f.endswith(".png"))

#         base_names = set()

#         # Define suffixes we need to check for each base
#         suffixes = ["_crop", "_crop_mask"]

#         # Checks for a single file if all the suffixes exist
#         def has_all_files(base, ext):
#             for suffix in suffixes:
#                 if f"{base}{suffix}.{ext}" not in files:
#                     return False
#             return True

#         # Iterate over all files and extract possible bases
#         candidates = set()
#         for f in files:
#             if f.endswith(".jpg"):
#                 candidates.add(f[:-4])  # remove .jpg
#             #elif f.endswith(".png"):
#             #    candidates.add(f[:-4])  # remove .png

#         valid_bases = set()

#         for base in candidates:
#             # Check for jpg
#             if has_all_files(base, "jpg"):
#                 valid_bases.add(base)
#             # Check for png
#             #elif has_all_files(base, "png"):
#             #    valid_bases.add(base)

#         # Sort base names before return
#         return JSONResponse(content=sorted(valid_bases))

#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=500)

from fastapi.responses import StreamingResponse
import pandas as pd
import io



@app.get("/get_image_set/{image_name}")
async def get_image_set(image_name: str):
    base_dir = "path/to/your/images"  # Update to actual directory

    # Construct expected file names
    image_set = {
        "original": f"{image_name}.jpg",  # or .png depending on your case
        "original_mask": f"{image_name}_mask.jpg",
        "crop": f"{image_name}_crop.jpg",
        "crop_mask": f"{image_name}_crop_mask.jpg"
    }

    image_urls = {}
    for key, filename in image_set.items():
        file_path = os.path.join(base_dir, filename)
        if os.path.exists(file_path):
            image_urls[key] = f"/static/images/{filename}"  # Assumes you're serving images via static
        else:
            image_urls[key] = None  # Or raise 404 depending on needs

    return JSONResponse(content=image_urls)

@app.get("/get_skin_disease_data/") # Keeping the endpoint name consistent
async def get_skin_disease_data(db: Session = Depends(get_db)):
    """
    Retrieves all skin disease image entries from the database as JSON.
    Includes all fields from the SkinDiseaseImage model.
    """
    images = db.query(SkinDiseaseImage).all()
    if not images:
        raise HTTPException(status_code=404, detail="No entries found in the skin disease table.")

    # Convert SQLAlchemy objects to a list of dictionaries, including all fields
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
            "created_at": image.created_at.isoformat() if image.created_at else None # Handle datetime serialization
        })

    return JSONResponse(content=data)


@app.get("/get_categorized_excel_data/")
def get_categorized_excel_data(db: Session = Depends(get_db)):
    # Now DoctorImageValidation is directly imported, so you don't need 'models.' prefix
    images = db.query(DoctorImageValidation).all()
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No entries found in the doctor image validation table.")

    # Use only defined column names for DoctorImageValidation
    # You also need to directly refer to DoctorImageValidation here, not models.DoctorImageValidation
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

# Source directory for crop images to be categorized
SOURCE_CROP_IMAGES_DIR = os.path.join(BASE_IMAGE_DIR, "categorize_images_crops")
CROP_IMAGES_DIR = SOURCE_CROP_IMAGES_DIR
# Destination directory for categorized crop images
CATEGORIZED_CROP_IMAGES_DIR = os.path.join(BASE_IMAGE_DIR, "categorized_images_crops_categorized")

# Ensure target directories exist
os.makedirs(SOURCE_CROP_IMAGES_DIR, exist_ok=True)
os.makedirs(CATEGORIZED_CROP_IMAGES_DIR, exist_ok=True)

##### CATEGORIZED IMAGES CROPS BATCH
import logging
logger = logging.getLogger(__name__)

@app.get("/get_crop_image_batch", response_model=List[str])
async def get_crop_image_batch(db: Session = Depends(get_db)): # Add db dependency if querying DB
    logger.info(f"Attempting to get crop image batch from directory: {CROP_IMAGES_DIR}")
    try:
        # **This is where your actual image fetching logic should be.**
        # **Replace this placeholder with how you get your initial image list.**

        # Example 1: Reading from a directory (MOST LIKELY SCENARIO FOR YOU)
        if not os.path.exists(CROP_IMAGES_DIR):
            logger.error(f"Image directory does NOT exist: {CROP_IMAGES_DIR}")
            raise HTTPException(status_code=500, detail=f"Image directory not found: {CROP_IMAGES_DIR}")

        all_image_filenames = [
            f for f in os.listdir(CROP_IMAGES_DIR)
            if os.path.isfile(os.path.join(CROP_IMAGES_DIR, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]
        all_image_filenames.sort()

        # Example 2: Querying from SkinDiseaseImage table (if your images are tracked in DB)
        # For this to work, ensure SkinDiseaseImage model has an 'image_name' column that is the filename
        # images_from_db = db.query(SkinDiseaseImage).filter(SkinDiseaseImage.is_categorized == False).limit(100).all() # Example filter
        # all_image_filenames = [img.image_name for img in images_from_db if img.image_name]


        logger.info(f"Found {len(all_image_filenames)} image files to return.")
        logger.debug(f"Image filenames: {all_image_filenames[:5]}...")

        # Directly return the list of strings
        return all_image_filenames # <--- THIS IS THE FIX. Just return the list of strings.

    except Exception as e:
        logger.exception("Error in get_crop_image_batch endpoint:")
        raise HTTPException(status_code=500, detail=f"Error retrieving image batch: {str(e)}")

from app.schemas import CropImageValidationResponse
@app.post("/submit_batch_categorization", response_model=List[CropImageValidationResponse])
def submit_batch_categorization(
    payloads: List[CropImageValidationRequest],
    db: Session = Depends(get_db)
):
    """
    Receives a list of categorizations, moves the images, and saves data to the DB.
    """
    records_to_add = [] # List to hold SQLAlchemy objects before commit
    
    for payload in payloads:
        original_filename = payload.image_filename
        src_path = os.path.join(SOURCE_CROP_IMAGES_DIR, original_filename)

        if not os.path.exists(src_path):
            print(f"Warning: Image {original_filename} not found at {src_path}. Skipping.")
            continue # Skip this image

        new_filename, new_abs_path = move_with_unique_name(src_path, CATEGORIZED_CROP_IMAGES_DIR)

        if not new_filename:
            print(f"Warning: Could not move image {original_filename}. Skipping.")
            continue

        image_db_path = f"/images/categorized_images_crops_categorized/{new_filename}"

        db_record = CropImageValidation(
            image_filename = payload.image_filename,
            image_path=image_db_path, # This is the image's path in the database
            doctor_name=payload.doctor_name,
            comments=payload.comments,
            crop_diagnosis=payload.crop_diagnosis,
            fitzpatrick_scale=None, #payload.fitzpatrick_scale,
            created_at=datetime.now(timezone.utc) # <--- Use timezone.utc here
        )
        records_to_add.append(db_record)

    try:
        db.add_all(records_to_add) # Add all records to the session
        db.commit() # Commit once for the whole batch
        
        responses_to_return = []
        for record in records_to_add:
            db.refresh(record) # Refresh each record to get its DB-generated ID and created_at

            # Explicitly create the Pydantic response object
            responses_to_return.append(
                CropImageValidationResponse(
                    id=record.id,
                    image_filename=os.path.basename(record.image_filename), # Extract filename from image_path
                    image_path=record.image_path,
                    doctor_name=record.doctor_name,
                    comments=record.comments,
                    crop_diagnosis=record.crop_diagnosis,
                    fitzpatrick_scale=record.fitzpatrick_scale,
                    created_at=record.created_at
                )
            )
        
        return responses_to_return # Return the list of Pydantic response objects

    except Exception as e:
        db.rollback()
        print(f"Database transaction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database error during batch submission: {e}")


@app.get("/get_excel_data_categorized_images_crops_batch/")
def get_categorized_excel_data(db: Session = Depends(get_db)):
    # Now DoctorImageValidation is directly imported, so you don't need 'models.' prefix
    images = db.query(CropImageValidation).all()
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No entries found in the doctor image validation table.")

    # Use only defined column names for DoctorImageValidation
    # You also need to directly refer to DoctorImageValidation here, not models.DoctorImageValidation
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
    data: DoctorImageValidationRequest, # Use the request schema
    db: Session = Depends(get_db),
):
    """
    Creates a new categorization entry in the database based on the provided data.
    The new entry will have a new ID. Image paths will be copied if needed.
    """
    # Create a new instance of the model with the data from the request
    # Note: 'id' and 'created_at' will be handled by the database (auto-increment/default)
    new_db_entry = DoctorImageValidation(
        image_path=None,#data.image_path, # These are crucial for the new entry
        mask_path=None,#data.mask_path,
        crop_path=data.crop_path,
        crop_mask_path=data.crop_mask_path,
        doctor_name=data.doctor_name,
        mask_rating = data.mask_rating,
        #rating=data.rating,
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
        created_at=datetime.utcnow()
    )

    db.add(new_db_entry)
    db.commit()
    db.refresh(new_db_entry)

    # You might want to handle file duplication here if the image_path/mask_path
    # needs to be physically duplicated for a "new" entry, rather than just referencing
    # the existing files. For now, it just creates a new DB record pointing to existing files.
    # If you need to duplicate files, you'd add os.path.copy2 logic here,
    # and update new_db_entry.image_path and new_db_entry.mask_path accordingly.

    return new_db_entry


from app.schemas import BatchCropImageRatingRequest, CropImageMetadata
from app.models import CropImageRating
from sqlalchemy.exc import IntegrityError

# @app.get("/crop_images_for_validation/", response_model=List[CropImageMetadata])
# async def get_crop_images_for_validation(
#     offset: int = 0,
#     limit: int = 15,
#     db: Session = Depends(get_db)
# ):
#     all_image_filenames = [f for f in os.listdir(CROP_IMAGES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
#     all_image_filenames.sort()

#     # Get paths of images already rated from the NEW table name
#     validated_image_paths = db.query(CropImageRating.image_path).all() # <--- CHANGED MODEL HERE
#     validated_image_paths_set = {path[0] for path in validated_image_paths}

#     unvalidated_image_filenames = [
#         f for f in all_image_filenames
#         if f"/image/classify_skin_disease_crops_images/{f}" not in validated_image_paths_set
#     ]

#     batch_filenames = unvalidated_image_filenames[offset : offset + limit]

#     image_metadata_list = [
#         CropImageMetadata(image_path=f"/image/classify_skin_disease_crops_images/{filename}")
#         for filename in batch_filenames
#     ]

#     return image_metadata_list



# @app.post("/submit_crop_validations/", status_code=status.HTTP_201_CREATED)
# async def submit_crop_validations(
#     batch_data: BatchCropImageRatingRequest, # <--- CHANGED SCHEMA HERE
#     db: Session = Depends(get_db)
# ):
#     new_entries = []
#     for rating_data in batch_data.validations: # Renamed loop variable for clarity
#         try:
#             # Check if an entry for this image_path already exists in the NEW table name
#             existing_entry = db.query(CropImageRating).filter( # <--- CHANGED MODEL HERE
#                 CropImageRating.image_path == rating_data.image_path
#             ).first()

#             if existing_entry:
#                 print(f"Warning: Rating for {rating_data.image_path} already exists. Skipping or updating.")
#                 continue

#             new_entry = CropImageRating( # <--- CHANGED MODEL HERE
#                 image_path=rating_data.image_path,
#                 doctor_name=rating_data.doctor_name,
#                 comments=rating_data.comments,
#                 crop_quality_rating=rating_data.crop_quality_rating,
#                 crop_diagnosis=rating_data.crop_diagnosis,
#             )
#             db.add(new_entry)
#             new_entries.append(new_entry)

#         except IntegrityError:
#             db.rollback()
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail=f"Rating for image {rating_data.image_path} already exists."
#             )
#         except Exception as e:
#             db.rollback()
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Error processing rating for {rating_data.image_path}: {str(e)}"
#             )

#     db.commit()
#     for entry in new_entries:
#         db.refresh(entry)

#     return {"message": f"Successfully processed {len(new_entries)} ratings."}

# Directory containing the original unvalidated crop images
CROP_IMAGES_SOURCE_DIR = os.path.join("images", "classify_skin_disease_crops_images")

# New directory where categorized crop images will be moved
CATEGORIZED_CROP_IMAGES_DIR = os.path.join(CROP_IMAGES_SOURCE_DIR, "categorized")

# Ensure the necessary directories exist
os.makedirs(CROP_IMAGES_SOURCE_DIR, exist_ok=True)
os.makedirs(CATEGORIZED_CROP_IMAGES_DIR, exist_ok=True)


def get_unique_filename(directory: str, original_filename: str) -> str:
    """
    Generates a unique filename in the given directory by appending a numerical suffix
    if a file with the original_filename already exists.
    e.g., 'image.jpg' -> 'image_1.jpg' -> 'image_2.jpg'
    """
    name, ext = os.path.splitext(original_filename)
    counter = 1
    new_filename = original_filename
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{name}_{counter}{ext}"
        counter += 1
    return new_filename


# Route to get a batch of RANDOM crop image paths for validation
@app.get("/crop_images_for_validation/", response_model=List[CropImageMetadata])
async def get_crop_images_for_validation(
    limit: int = 15,
    db: Session = Depends(get_db)
):
    """
    Fetches a batch of RANDOM crop image paths that have NOT yet been
    validated (i.e., not in the crop_image_rating table).
    """
    all_image_filenames = [
        f for f in os.listdir(CROP_IMAGES_SOURCE_DIR)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')) and
           os.path.isfile(os.path.join(CROP_IMAGES_SOURCE_DIR, f))
    ]
    all_image_filenames.sort()

    rated_image_urls = db.query(CropImageRating.image_path).all()
    rated_image_urls_set = {url[0] for url in rated_image_urls}

    unrated_image_filenames = []
    for filename in all_image_filenames:
        full_image_url_path = f"/images/classify_skin_disease_crops_images/{filename}"
        if full_image_url_path not in rated_image_urls_set:
            unrated_image_filenames.append(filename)

    random_batch_filenames = random.sample(unrated_image_filenames, min(limit, len(unrated_image_filenames)))

    image_metadata_list = [
        CropImageMetadata(image_path=f"/images/classify_skin_disease_crops_images/{filename}")
        for filename in random_batch_filenames
    ]

    return image_metadata_list

# Route to submit a batch of crop image rating data and move the files
@app.post("/submit_crop_validations/", status_code=status.HTTP_201_CREATED)
async def submit_crop_validations(
    batch_data: BatchCropImageRatingRequest,
    db: Session = Depends(get_db)
):
    """
    Receives a batch of crop image rating data, stores it in the database,
    and moves the physically rated image files to the categorized directory,
    handling filename conflicts.
    """
    new_db_entries_count = 0
    moved_files_count = 0
    errors = []

    for rating_data in batch_data.validations:
        try:
            # 1. Check if an entry for this image_path already exists in the database
            existing_entry = db.query(CropImageRating).filter(
                CropImageRating.image_path == rating_data.image_path
            ).first()

            if existing_entry:
                print(f"Warning: Rating for {rating_data.image_path} already exists. Skipping database entry and file move.")
                continue

            # 2. Create new database entry
            new_entry = CropImageRating(
                image_path=rating_data.image_path,
                doctor_name=rating_data.doctor_name,
                comments=rating_data.comments,
                crop_quality_rating=rating_data.crop_quality_rating,
                crop_diagnosis=rating_data.crop_diagnosis,
            )
            db.add(new_entry)
            new_db_entries_count += 1

            # 3. Move the physical image file
            relative_file_path_from_base_static = rating_data.image_path.replace("/images/", "", 1)
            source_file_abs_path = os.path.join("images", relative_file_path_from_base_static)

            if not os.path.exists(source_file_abs_path):
                print(f"File not found for moving: {source_file_abs_path}. Skipping file move.")
                errors.append(f"File not found for {rating_data.image_path}. (DB entry added)")
                continue # Do not attempt to move if source file doesn't exist

            # --- Apply unique filename logic here ---
            original_basename = os.path.basename(source_file_abs_path)
            unique_filename_for_destination = get_unique_filename(CATEGORIZED_CROP_IMAGES_DIR, original_basename)
            destination_file_abs_path = os.path.join(CATEGORIZED_CROP_IMAGES_DIR, unique_filename_for_destination)

            shutil.move(source_file_abs_path, destination_file_abs_path)
            moved_files_count += 1
            print(f"DEBUG: Moved {source_file_abs_path} to {destination_file_abs_path}")

        except IntegrityError:
            db.rollback()
            errors.append(f"Duplicate entry for image {rating_data.image_path}. This image might have been processed concurrently.")
            print(f"Error: IntegrityError for {rating_data.image_path}. Rolled back.")
        except FileNotFoundError as e:
            db.rollback()
            errors.append(f"File system error (file not found/permissions) for {rating_data.image_path}: {str(e)}")
            print(f"Error: FileNotFoundError for {rating_data.image_path}: {str(e)}. Rolled back.")
        except Exception as e:
            db.rollback()
            errors.append(f"Unexpected error processing {rating_data.image_path}: {str(e)}")
            print(f"Error: Unexpected exception for {rating_data.image_path}: {str(e)}. Rolled back.")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        errors.append(f"Final database commit failed: {str(e)}")
        print(f"Error: Final DB commit failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to commit some data: {'; '.join(errors) if errors else 'Unknown error'}"
        )

    message = f"Successfully processed {new_db_entries_count} ratings. {moved_files_count} files moved."
    if errors:
        message += f" Some issues occurred: {', '.join(errors)}"
        raise HTTPException(
            status_code=status.HTTP_207_MULTI_STATUS,
            detail={"message": message, "errors": errors}
        )

    return {"message": message}


@app.get("/get_excel_data_categorized_doctor_skin_disease_crops_rating_batch/")
def get_categorized_excel_data(db: Session = Depends(get_db)):
    # Now DoctorImageValidation is directly imported, so you don't need 'models.' prefix
    images = db.query(CropImageRating).all()
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No entries found in the doctor image validation table.")

    # Use only defined column names for DoctorImageValidation
    # You also need to directly refer to DoctorImageValidation here, not models.DoctorImageValidation
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

# Directory for images to be rated by crop quality (new source for this task)
CROP_QUALITY_RATING_SOURCE_DIR = os.path.join(STATIC_DIR, "crop_quality_rating_images")

# Destination directory for images after they are rated by crop quality
CROP_QUALITY_RATING_CHECKED_DIR = os.path.join(CROP_QUALITY_RATING_SOURCE_DIR, "checked")

# Existing directory for batch image validation (from previous task)
CROP_IMAGES_SOURCE_DIR = os.path.join(STATIC_DIR, "classify_skin_disease_crops_images")
CATEGORIZED_CROP_IMAGES_DIR = os.path.join(CROP_IMAGES_SOURCE_DIR, "categorized")


# Ensure directories exist
os.makedirs(CROP_QUALITY_RATING_SOURCE_DIR, exist_ok=True)
os.makedirs(CROP_QUALITY_RATING_CHECKED_DIR, exist_ok=True)

# --- ROUTE: Get a single random unrated image for crop quality rating ---
@app.get("/get_next_crop_quality_rating_image/", response_model=Optional[SingleCropImageMetadata])
async def get_next_crop_quality_rating_image(db: Session = Depends(get_db)):
    """
    Fetches a single random image path from 'crop_quality_rating_images' that
    has not yet been rated in the 'crop_image_quality_rating' table.
    """
    all_image_filenames = [
        f for f in os.listdir(CROP_QUALITY_RATING_SOURCE_DIR)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')) and
           os.path.isfile(os.path.join(CROP_QUALITY_RATING_SOURCE_DIR, f))
    ]
    all_image_filenames.sort()

    # Query the NEW table name: models.CropImageQualityRating
    rated_image_urls = db.query(CropImageQualityRating.image_path).filter(
        CropImageQualityRating.image_path.like(f"/images/crop_quality_rating_images/%")
    ).all()
    rated_image_urls_set = {url[0] for url in rated_image_urls}

    unrated_image_filenames = []
    for filename in all_image_filenames:
        full_image_url_path = f"/images/crop_quality_rating_images/{filename}"
        if full_image_url_path not in rated_image_urls_set:
            unrated_image_filenames.append(filename)

    if not unrated_image_filenames:
        return None # No more unrated images

    random_filename = random.choice(unrated_image_filenames)
    image_path_for_response = f"/images/crop_quality_rating_images/{random_filename}"

    return SingleCropImageMetadata(image_path=image_path_for_response)


# --- ROUTE: Submit a single crop quality rating and move the file ---
@app.post("/submit_crop_quality_rating/", status_code=status.HTTP_201_CREATED)
async def submit_crop_quality_rating(
    rating_data: SingleCropQualityRatingRequest,
    db: Session = Depends(get_db)
):
    """
    Receives a single crop image quality rating, stores it in the database,
    and moves the physically rated image file to the 'checked' directory.
    """
    try:
        # Query the NEW table name: models.CropImageQualityRating
        existing_entry = db.query(CropImageQualityRating).filter(
            CropImageQualityRating.image_path == rating_data.image_path
        ).first()

        if existing_entry:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Image {rating_data.image_path} has already been rated."
            )

        # Create new database entry using the NEW model: models.CropImageQualityRating
        new_entry = CropImageQualityRating(
            image_path=rating_data.image_path,
            doctor_name=rating_data.doctor_name,
            comments=rating_data.comments,
            crop_quality_rating=rating_data.crop_quality_rating,

        )
        db.add(new_entry)
        db.commit() # Commit immediately for single entry
        db.refresh(new_entry)

        relative_file_path_from_base_static = rating_data.image_path.replace("/images/", "", 1)
        source_file_abs_path = os.path.join(STATIC_DIR, relative_file_path_from_base_static)

        if not os.path.exists(source_file_abs_path):
            print(f"File not found for moving: {source_file_abs_path}. DB entry created, but file not moved.")
            return {"message": f"Rating saved, but file {os.path.basename(source_file_abs_path)} not found for moving."}

        original_basename = os.path.basename(source_file_abs_path)
        unique_filename_for_destination = get_unique_filename(CROP_QUALITY_RATING_CHECKED_DIR, original_basename)
        destination_file_abs_path = os.path.join(CROP_QUALITY_RATING_CHECKED_DIR, unique_filename_for_destination)

        shutil.move(source_file_abs_path, destination_file_abs_path)
        print(f"DEBUG: Moved {source_file_abs_path} to {destination_file_abs_path}")

        return {"message": "Rating submitted and image moved successfully!"}

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Rating for image {rating_data.image_path} already exists. Cannot re-rate."
        )
    except FileNotFoundError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File system error (file not found/permissions) for {rating_data.image_path}: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        print(f"Error processing rating for {rating_data.image_path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error processing rating for {rating_data.image_path}: {str(e)}"
        )

from app.models import CropImageQualityRating


@app.get("/get_excel_data_categorized_doctor_skin_disease_crops_rating_single_image/")
def get_categorized_excel_data(db: Session = Depends(get_db)):
    # Now DoctorImageValidation is directly imported, so you don't need 'models.' prefix
    images = db.query(CropImageQualityRating).all()
    if not images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No entries found in the doctor image validation table.")

    # Use only defined column names for DoctorImageValidation
    # You also need to directly refer to DoctorImageValidation here, not models.DoctorImageValidation
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
    """
    Returns a list of subdirectory names within the BASE_STATIC_DIR.
    """
    subdirectories = []
    try:
        # List all entries in the base static directory
        for entry in os.listdir(STATIC_DIR):
            full_path = os.path.join(STATIC_DIR, entry)
            # Check if it's a directory and not a hidden directory (e.g., .git, .DS_Store)
            if os.path.isdir(full_path) and not entry.startswith('.'):
                subdirectories.append(entry)
        subdirectories.sort() # Keep them sorted alphabetically
    except Exception as e:
        print(f"Error listing subdirectories: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve subdirectories.")
    return subdirectories


import os
import shutil
from typing import List, Optional
from fastapi import UploadFile, File, Form, HTTPException, status
from fastapi.responses import HTMLResponse # Ensure HTMLResponse is imported for the root route
from fastapi.staticfiles import StaticFiles
from pathlib import Path # For robust path handling

# --- EXISTING ROUTE: Handle Image Uploads ---
@app.post("/upload_images/")
async def upload_images(
    files: List[UploadFile] = File(...), # List of uploaded files
    subdirectory: Optional[str] = Form(None) # Optional subdirectory name from form data
):
    """
    Uploads one or more image files to a specified subdirectory within the BASE_STATIC_DIR.
    If no subdirectory is provided, files are uploaded directly to BASE_STATIC_DIR.
    """
    uploaded_file_names = []
    
    # Determine the target directory
    if subdirectory:
        # Sanitize subdirectory name to prevent path traversal attacks
        # Path.as_posix() converts to forward slashes, and ".." check prevents going up
        sanitized_subdirectory = Path(subdirectory).as_posix()
        if ".." in sanitized_subdirectory or sanitized_subdirectory.startswith("/"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subdirectory name.")
        
        target_directory = os.path.join(STATIC_DIR, sanitized_subdirectory)
    else:
        target_directory = STATIC_DIR

    # Create the target directory if it doesn't exist
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

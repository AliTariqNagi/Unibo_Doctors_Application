# Unibo_Doctors_Application

# Setting Up the DB
sudo apt update   
sudo apt install postgresql postgresql-contrib  
sudo systemctl status postgresql  
sudo -i -u postgres  
psql  
CREATE DATABASE doctor_image_validation;  
CREATE USER admin WITH PASSWORD 'admin';  
GRANT ALL PRIVILEGES ON DATABASE doctor_image_validation TO admin;  
\q  

# Running the project

pm2 stop backend
pm2 delete backend
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 80" --name backend
pm2 logs backend --lines 20

# Running the Project for the first time
Move images from the Unibo_Doctors_Application/images/disease and Unibo_Doctors_Application/images/non-disease folders to Unibo_Doctors_Application/images


# Application
From the browser please enter the address
https://medicalimages.apice.unibo.it/frontend/main.html  
Username: admin  
Password: password  

# Upload Images to the Server
The command to upload images for the module 1 (Categorize Images) is:
scp ./images/* root@192.168.15.7:'/root/Unibo_Doctor_App/Unibo_Doctors_Application-main (1) (2)/Unibo_Doctors_Application-main/images'

Where ./images is the local folder which contain all the image files
Each images should have four formats:
image_name.jpg,
image_name_mask.jpg,
image_name_crop.jpg,
image_name_crop_mask.jpg


# Download the Project Folder to local computer
tar -czvf my_selected_project.tar.gz app frontend
$ scp root@192.168.15.7:'/root/Unibo_Doctor_App/Unibo_Doctors_Application-main (1) (2)/Unibo_Doctors_Application-main/my_selected_project.tar.gz' .

# Downloading files from the project 
## Project
scp -r root@192.168.15.7:'/root/Unibo_Doctor_App/Unibo_Doctors_Application-main (1) (2)/Unibo_Doctors_Application-main' .
## Files
scp -r root@192.168.15.7:'/root/Unibo_Doctor_App/Unibo_Doctors_Application-main (1) (2)/Unibo_Doctors_Application-main/app/*.py' .

# Uploading files to the directory
scp main.py root@192.168.15.7:'/root/Unibo_Doctor_App/Unibo_Doctors_Application-main (1) (2)/Unibo_Doctors_Application-main/app/' 

# Categorize Images
## Frontend file: categorize_images.html
## Source Images Directory: /images/categorized_images
   Expect Images: {base_name}.jpg, {base_name}_mask.jpg, {base_name}_crop.jpg, {base_name}_crop_mask.jpg
## Target Images Directory: /images/categorized_images_crops_categorized
## Table Name: doctor_image_validation
### Table Fields:
#### id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String)
    mask_path = Column(String)
    crop_path = Column(String)            # New
    crop_mask_path = Column(String)       # New

    doctor_name = Column(String)
    #rating = Column(Integer)
    comments = Column(String)
    mask_comments = Column(String)
    disease_name = Column(String)
    category = Column(String)
    created_at = Column(DateTime, server_default=func.now())

    #years_of_experience = Column(Integer)   
    real_generated = Column(String)
    realism_rating = Column(Integer)
    image_precision = Column(String)
    skin_color_precision = Column(Integer)
    confidence_level = Column(Integer)
    crop_quality_rating = Column(Integer)
    crop_diagnosis = Column(String)
    fitzpatrick_scale = Column(String)



# Download Initial Excel
## Frontend file: download_categorized_excel.html
## Table Name: doctor_image_validation


# View/Edit Images Details
## Creates new entries in the tables for the modifications
## Frontend file: view_edit_images.html
## Table Name: doctor_image_validation

# Categorize Images Crops
## Frontend file: categorized_images_crops_batch.html
## Source Images Directory: /images/categorize_images_crops/ 
## Target Directory: /images/categorized_images_crops_categorized
### Get 15 files from this directory
   Expect Images: {base_name}.jpg
## Target Images Directory: /images/categorized_images_crops_categorized/
## Table Name: crop_image_validation
### Table Fields:
####     
    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String) # Path to the categorized crop image
    doctor_name = Column(String)
    comments = Column(String)
    crop_diagnosis = Column(String)
    fitzpatrick_scale = Column(String)
    created_at = Column(DateTime, server_default=func.now())


# Download Categorize Images Crops
## Frontend file: download_categorized_images_crops_batch.html
## Table Name: crop_image_validation
### Table Fields:
####     
    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String) # Path to the categorized crop image
    doctor_name = Column(String)
    comments = Column(String)
    crop_diagnosis = Column(String)
    fitzpatrick_scale = Column(String)
    created_at = Column(DateTime, server_default=func.now())


# Skin Disease Crops Rating
Get Random 15 files 
## Frontend file: doctor_skin_disease_crops_rating.html
## Source Images Directory: /images/classify_skin_disease_crops_images
   Expect Images: {base_name}.jpg
## Target Images Directory: /images/classify_skin_disease_crops_images/categorized
## Table Name: crop_image_rating
### Table Fields:
#### 
   id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, unique=True, index=True)
    doctor_name = Column(String)
    comments = Column(String)
    crop_quality_rating = Column(Integer)
    crop_diagnosis = Column(String)
    created_at = Column(DateTime, server_default=func.now())



# Download Excel Skin Disease Crops Rating
## Frontend file: doctor_skin_disease_crops_rating_download_excel.html
## Table Name: crop_image_rating
### Table Fields:
#### 
   id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, unique=True, index=True)
    doctor_name = Column(String)
    comments = Column(String)
    crop_quality_rating = Column(Integer)
    crop_diagnosis = Column(String)
    created_at = Column(DateTime, server_default=func.now())




# Crop Quality Rating
## Frontend file: crop_quality_rating.html
## Source Images Directory: /images/crop_quality_rating_images
   Expect Images: {base_name}.jpg
## Target Images Directory: /images/crop_quality_rating_images/checked
## Table Name: crop_image_quality_rating
### Table Fields:
#### 
    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, unique=True, index=True)
    doctor_name = Column(String)
    comments = Column(String)
    crop_quality_rating = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())



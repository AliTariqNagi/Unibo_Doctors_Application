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
categorize_images.html
Source Images Directory: /images/categorized_images
Target Images Directory: /images/categorized_images_crops_categorized




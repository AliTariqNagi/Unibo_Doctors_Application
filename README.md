# Image Categorization for Dermatology
# Unibo_Doctors_Image_Categorization_Application


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



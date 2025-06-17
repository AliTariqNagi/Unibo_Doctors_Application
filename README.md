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
Running the frontend server  
cd frontend  
python3 -m http.server 8080  
  
Running the Backend server  
uvicorn app.main:app --reload  
###uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
 pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" --name backend
root@UniboDoctorsApp:~/Unibo_Doctor_App/Unibo_Doctors_Application-main (1) (2)/Unibo_Doctors_Application-main/frontend# pm2 start "python3 -m http.server 8080" --name frontend


pm2 delete frontend  # optional, if already running
pm2 start "python3 -m http.server 80" --name frontend

pm2 save
pm2 startup

# Running the Project for the first time
Move images from the Unibo_Doctors_Application/images/disease and Unibo_Doctors_Application/images/non-disease folders to Unibo_Doctors_Application/images


# Application
From the browser please enter the address
http://localhost:8080/main.html  
Username: admin  
Password: password  

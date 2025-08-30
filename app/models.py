from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func

# sqlalchemy to connect with the Postgresql
# it is essential to create an engine object, that serves as a central source of connection by providing a connection pool 
# that manages the database connections. This SQLAlchemy engine is a global object which can be created and configured once 
# and use the same engine object multiple times for different operations.
# engine = create_engine(dialect+driver://username:password@host:port/database_name)
# The Engine establishes a real DBAPI connection to the database when a method like Engine.execute() or Engine.connect() is called.
engine = create_engine("postgresql://admin:admin@localhost/doctor_image_validation")


# In order to interact with the database, we need to obtain its handle. A session object is the handle to database. 
# Session class is defined using sessionmaker() a configurable session factory method which is bound to the engine object created earlier.
# from sqlalchemy.orm import sessionmaker
# Session = sessionmaker(bind = engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# The session object is then set up using its default constructor as follows −
# session = Session()

# Some of the frequently required methods of session class are listed below −
# 1	begin() begins a transaction on this session
# 2	add() places an object in the session. Its state is persisted in the database on next flush operation
# 3	add_all() adds a collection of objects to the session
# 4 commit() flushes all items and any transaction in progress
# 5	delete() marks a transaction as deleted
# 6	execute() executes a SQL expression
# 7	expire() marks attributes of an instance as out of date
# 8	flush() flushes all object changes to the database
# 9	invalidate() closes the session using connection invalidation
# 10 rollback() rolls back the current transaction in progress
# 11 close() Closes current session by clearing all items and ending any transaction in progress


# the configurational process starts by describing the database tables and then by defining classes which will be mapped to those tables
#In SQLAlchemy, these two tasks are performed together. This is done by using Declarative system; the classes created include directives 
#to describe the actual database table they are mapped to.
# A base class stores a catlog of classes and mapped tables in the Declarative system. This is called as the declarative base class. There 
# will be usually just one instance of this base in a commonly imported module. The declarative_base() function is used to create base class. 
# This function is defined in sqlalchemy.ext.declarative module.
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


# using Declarative system; 
# the classes created include directives to describe the actual database table they are mapped to
# Once base classis declared, any number of mapped classes can be defined in terms of it.
# Following code defines a Customers class. It contains the table to be mapped to, and names and 
# datatypes of columns in it.
# class Customers(Base):
#    __tablename__ = 'customers'
   
#    id = Column(Integer, primary_key = True)
#    name = Column(String)
#    address = Column(String)
#    email = Column(String)

#########--------------------------------------Doctors Class Mapped to "doctors" Table----------------------------------###################
# A class in Declarative must have a __tablename__ attribute, and at least one Column which is part of a primary key
# This mapped class like a normal Python class has attributes and methods as per the requirement.
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
#########----------------------------------------------------------------------------------------------------------------###################



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
    mask_name = Column(String)
    image_path = Column(String, nullable=False)
    mask_path = Column(String)
    crop_image_name = Column(String)
    crop_image_path = Column(String)
    crop_mask_name = Column(String)
    crop_mask_path = Column(String)
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
    __tablename__ = "crop_image_validation" 

    id = Column(Integer, primary_key=True, index=True)
    image_filename = Column(String)
    image_path = Column(String)
    doctor_name = Column(String)
    comments = Column(String)
    crop_diagnosis = Column(String)
    fitzpatrick_scale = Column(String)
    confidence = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())



class CropImageRating(Base): 
    __tablename__ = "crop_image_rating" 

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String)
    doctor_name = Column(String)
    comments = Column(String)
    crop_quality_rating = Column(Integer)
    crop_diagnosis = Column(String)
    confidence = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())


class CropImageQualityRating(Base): 
    __tablename__ = "crop_image_quality_rating"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String)
    doctor_name = Column(String)
    comments = Column(String)
    crop_quality_rating = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())


# Declarative replaces all the Column objects with special Python accessors known as descriptors. 
# This process is known as instrumentation which provides the means to refer to the table in a SQL 
# context and enables persisting and loading the values of columns from the database.

# The information about class in Declarative system, is called as table metadata. SQLAlchemy uses Table object to 
# represent this information for a specific table created by Declarative. The Table object is created according to 
# the specifications, and is associated with the class by constructing a Mapper object. This mapper object is not 
# directly used but is used internally as interface between mapped class and table.
# Each Table object is a member of larger collection known as MetaData and this object is available using the .metadata 
# attribute of declarative base class.

# The MetaData.create_all() method is, using Engine as parameter for a database connectivity.
#  
# For all tables that havent been created yet, it issues CREATE TABLE statements to the database.
Base.metadata.create_all(bind=engine)



# The complete script to create a database and a table, and to map Python class is given below −
# from sqlalchemy import Column, Integer, String
# from sqlalchemy import create_engine
# engine = create_engine('sqlite:///sales.db', echo = True)
# from sqlalchemy.ext.declarative import declarative_base
# Base = declarative_base()

# class Customers(Base):
#    __tablename__ = 'customers'
#    id = Column(Integer, primary_key=True)

#    name = Column(String)
#    address = Column(String)
#    email = Column(String)
# Base.metadata.create_all(engine)

# When executed, Python console will print following SQL expression being executed −
# CREATE TABLE customers (
#    id INTEGER NOT NULL,
#    name VARCHAR,
#    address VARCHAR,
#    email VARCHAR,
#    PRIMARY KEY (id)
# )
from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import Config 

#creates flask app instance 
app = Flask(__name__) 

#Loads configuration from config class
#this incuds URI and secret key
app.config.from_object(Config) 

# Initialize extensions 

#connects MongoDB to flask 
mongo = PyMongo(app) 

#enables passwrod hashing and verification 
bcrypt = Bcrypt(app) 


#Initialize flask login 
login_manager = LoginManager(app) 

#specifies the login route 
#if user tries to access a protected page, such as trying to access /home without logging in, it will redirect to login page 
login_manager.login_view = 'login' 


# Import routes to ensure that the app has endppoints registered 
from routes import *

if __name__ == "__main__":
    app.run(debug=True)

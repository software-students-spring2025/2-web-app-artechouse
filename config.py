import os 
from dotenv import load_dotenv
class Config: 

  #configuration setup to setup MongoDB and flask-login 
  
  load_dotenv()  

  MONGO_URI = os.getenv("MONGO_URI")
  SECRET_KEY = os.getenv("SECRET_KEY")

  






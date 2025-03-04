from flask_login import UserMixin
from app import mongo

#class to set user information 
#Clas s inherits UserMixin, meaning built-in authentication properties from flask-login 
class User(UserMixin):

    #constructor called when new user object is created  
    def __init__(self, user_data):
        self.id = str(user_data['_id'])  # MongoDB _id is an ObjectId, convert to string 

        #username and password from MongoDB document to User objects attributes 
        self.email = user_data['email']
        self.username = user_data['username']
        self.password = user_data['password']

    #can only be called inside the class (static method)
    @staticmethod
    def get_user(email):
        """Fetch a user from MongoDB""" 

        #refers finds user in user collection
        user_data = mongo.db.users.find_one({"email": email}) 

        #if user found, create new user object else, return None 
        return User(user_data) if user_data else None

from flask_login import UserMixin
from app import mongo

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])  # Convert MongoDB ObjectId to string
        self.email = user_data['email']  # Store email
        self.username = user_data['username']  # Store extracted username
        self.password = user_data['password']  # Store hashed password

    @staticmethod
    def get_user(email):
        """Fetch a user from MongoDB using email"""
        user_data = mongo.db.users.find_one({"email": email})  
        return User(user_data) if user_data else None

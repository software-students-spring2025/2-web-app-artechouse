from flask import render_template, request, redirect, url_for, flash, session, make_response
from flask_login import login_user, logout_user, login_required, current_user
from bson.objectid import ObjectId
from app import app, mongo, bcrypt, login_manager
from models import User 
import re


#Test/verify connection to database:  
@app.route('/test_db')
def test_db():
    try:
        collections = mongo.db.list_collection_names()
        return f"Connected to MongoDB! Collections: {collections}"
    except Exception as e:
        return f"Database connection error: {str(e)}"


@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login session"""
    user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    return User(user_data) if user_data else None 


@app.route('/')
@login_required
def home():
    response = make_response(render_template('home.html', username=current_user.username)) 
    response = make_response(render_template('home.html', username=current_user.username))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST': 
        email = request.form['email']
        password = request.form['password']
        
        # Fetch user by email
        user = User.get_user(email)  

        # If user exists and password matches hashed password
        if user and bcrypt.check_password_hash(user.password, password):  
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password", "danger")
    
    return render_template('login.html') 



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'] 

        # Ensure email ends with '@nyu.edu'
        if not re.match(r"^[a-zA-Z0-9._%+-]+@nyu\.edu$", email):
            flash("You must use an NYU email (@nyu.edu) to register.", "danger")
            return redirect(url_for('register'))

        
        # Extract username from email (everything before @)
        username = email.split('@')[0]

        # Check if email already exists in the database
        if mongo.db.users.find_one({"email": email}):
            flash("Email already registered!", "danger") 
        else:
            # Hash the password before storing it
            hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
            
            # Insert user into MongoDB with 'email' and extracted 'username'
            mongo.db.users.insert_one({
                "email": email,
                "username": username,  # Automatically extracted
                "password": hashed_pw
            })

            flash("Account created successfully!", "success")
            return redirect(url_for('login'))
        
    return render_template('register.html') 

@app.route('/logout')
@login_required
def logout():
    logout_user()  # Logs out the user
    # Create a response to prevent caching
    response = make_response(redirect(url_for('login')))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

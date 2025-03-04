from flask import render_template, request, redirect, url_for, flash, session, make_response
from flask_login import login_user, logout_user, login_required, current_user
from bson.objectid import ObjectId
from app import app, mongo, bcrypt, login_manager
from models import User


#Test/verify connection to database:  
@app.route('/test_db')
def test_db():
    try:
        collections = mongo.db.list_collection_names()
        return f"Connected to MongoDB! Collections: {collections}"
    except Exception as e:
        return f"Database connection error: {str(e)}"




#decorator telling flask how to laod user from MongoDB database to manage user sessions  

#called inside /login route 
@login_manager.user_loader 

#function to load the current user to check if it is in the database or not
def load_user(user_id): #flask-Login stores user-id in current session

    #database lookup: checks if connected database "mongo.db", within collections ".users" has one user with the same "_id"
    user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)}) 

    #If found, return the user object, else return None if account not found
    return User(user_data) if user_data else None 



@app.route('/') #redirect to login page if login fails
@login_required  #checker to access home page, user has to be logged in
def home():
    # Prevent browser from caching the page
    response = make_response(render_template('index.html')) 
    #username=current_user.username
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response



#GET display login page 
#POST processes login form submission
@app.route('/login', methods=['GET', 'POST'])
def login():
    
    #if the current request is processing the form
    if request.method == 'POST': 
        #initialize two variables getting username and password
        email = request.form.get('email', '').strip().lower()  
        password = request.form['password']
        
        #create user object fetching user info from database
        user = User.get_user(email) 

        #if user is in database and password matches hashed password in database
        if user and bcrypt.check_password_hash(user.password, password): 
            #login 
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password", "danger") 
            return redirect(url_for('login'))  # Prevents unnecessary processing

    return render_template('login.html') 


@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        email = request.form['email'].lower() #store in lower to ensure nyu.edu email 

        password = request.form['password']  
    
        # Extract username (everything before `@`)
        if "@" in email: 
            username = email.split('@')[0] 
            
        else:
            flash("Invalid email format.", "danger")  
            return redirect(url_for('register'))  

        
        #Check if email exists in collection 
        if mongo.db.users.find_one({"email": email}):
            flash("Email already exists!", "danger") 
            return redirect(url_for('register')) 
        
        #non nyu email
        if email.split('@')[-1] != "nyu.edu":
            flash("Please use an NYU email to sign up.")  
            return redirect(url_for('register')) 

        #hashes password for encryption
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8') 

        #insert user as a new query
        mongo.db.users.insert_one({"email" : email, "username": username, "password": hashed_pw}) 

        #send message showing account successfully made
        flash("Account created successfully!", "success")
        return redirect(url_for('login'))
        
    #renders and returns HTML page to user's browser
    return render_template('register.html') 

@app.route('/logout')
@login_required
def logout():
    logout_user() 
    session.clear()
    return redirect(url_for('login'))
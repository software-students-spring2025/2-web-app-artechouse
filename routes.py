from flask import render_template, request, redirect, url_for, flash, session, make_response
from flask_login import login_user, logout_user, login_required, current_user
from bson.objectid import ObjectId
from pymongo import MongoClient
import os
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

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DBNAME")]

# ----------------------------------------------------USER LOGIN-------------------------------------------------------

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
    books = list(db["books"].find({})) 
    response = make_response(render_template('index.html', books=books)) 
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

# ----------------------------------------------------ADD A BOOK-------------------------------------------------------

@app.route("/add-book", methods=["GET", "POST"])
def add_book():
    """
    Renders the add book form page and handles new book submissions.
    """
    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author")
        edition = request.form.get("edition")
        year = request.form.get("year")
        condition = request.form.get("condition")
        price = request.form.get("price")
        book_format = request.form.get("format")

        if not title or not author or not year or not price:
            return jsonify({"error": "Missing required fields"}), 400
            
        new_book = {
            "title": title,
            "author": author,
            "edition": edition,
            "year": int(year),
            "condition": condition,
            "price": float(price),
            "format": book_format,
            "seller_id": current_user.id,
            "status": "Available"
        }

        book_inserted = db.books.insert_one(new_book)
        book_id = book_inserted.inserted_id

        db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$push": {"listed_books": book_id}}  # Add book reference to the user's profile
        )


        return redirect(url_for("home"))
    return render_template("add_book.html")

# ----------------------------------------------------FETCH A BOOK-------------------------------------------------------

@app.route("/book/<book_id>")
def book_details(book_id):
    """
    Route to display the details of a selected book.
    """
    book = db.books.find_one({"_id": ObjectId(book_id)})
        
    if not book:
        return "Book not found", 404

    return render_template("book_details.html", book=book)

# ----------------------------------------------------MY LISTINGS-------------------------------------------------------
@app.route("/edit-book/<book_id>", methods=["GET", "POST"])
@login_required
def edit_book(book_id):
    """
    Allows the seller to edit a book listing.
    """
    book = db.books.find_one({"_id": ObjectId(book_id), "seller_id": current_user.id})
    
    if not book:
        flash("Book not found or unauthorized!", "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        updated_data = {
            "title": request.form.get("title"),
            "author": request.form.get("author"),
            "edition": request.form.get("edition"),
            "year": int(request.form.get("year")),
            "condition": request.form.get("condition"),
            "price": float(request.form.get("price")),
            "format": request.form.get("format"),
        }
        db.books.update_one({"_id": ObjectId(book_id)}, {"$set": updated_data})
        flash("Book listing updated successfully!", "success")
        return redirect(url_for("book_details", book_id=book_id))

    return render_template("edit_book.html", book=book)

# @app.route("/profile/book/<book_id>")
# def my_listings(book_id):
#     """
#     Route to display the details of a selected book.
#     """
#     book = db.books.find_one({"_id": ObjectId(book_id)})
        
#     if not book:
#         return "Book not found", 404

#     return render_template("book_details.html", book=book)

@app.route("/delete-book/<book_id>")
@login_required
def delete_book(book_id):
    """
    Allows the seller to delete a book listing.
    """
    book = db.books.find_one({"_id": ObjectId(book_id), "seller_id": current_user.id})

    if not book:
        flash("Book not found or unauthorized!", "danger")
        return redirect(url_for("home"))

    db.books.delete_one({"_id": ObjectId(book_id)})
    
    # Remove reference from user's listed_books
    db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$pull": {"listed_books": ObjectId(book_id)}}
    )

    flash("Book listing deleted successfully!", "success")
    return redirect(url_for("user_profile"))

@app.route("/mark-as-sold/<book_id>")
@login_required
def mark_as_sold(book_id):
    """
    Allows the seller to mark a book as sold.
    """
    book = db.books.find_one({"_id": ObjectId(book_id), "seller_id": current_user.id})

    if not book:
        flash("Book not found or unauthorized!", "danger")
        return redirect(url_for("home"))

    db.books.update_one({"_id": ObjectId(book_id)}, {"$set": {"status": "Sold"}})
    flash("Book marked as sold!", "success")
    return redirect(url_for("user_profile"))

# ----------------------------------------------------SEARCH-------------------------------------------------------

@app.route("/search-results", methods=["GET"])
def search_books():
    """
    Fetch books from the database based on search.
    """
    search_query = request.args.get("query", "").strip()

    if not search_query: #for empty search query
        return redirect(url_for("home"))

    # Convert to regular expression to make it case-insensitive
    query = {
        "$or": [
            {"title": {"$regex": search_query, "$options": "i"}},
            {"author": {"$regex": search_query, "$options": "i"}}
        ]
    }

    books = list(db.books.find(query))

    return render_template("index.html", books=books)

# ----------------------------------------------------FILTER/SORT-------------------------------------------------------

@app.route("/filter-sort")
def filter_sort():
    return render_template("filterAndSort.html")

@app.route("/filter-results", methods=["GET"])
def filter_results():
    """
    Fetch books from the database based on selected filters.
    """
    # Retrieve filter values from request arguments
    sort_by = request.args.get("sort")
    conditions = request.args.getlist("condition")  
    formats = request.args.getlist("format")  
    editions = request.args.getlist("edition")  

    # Build MongoDB query
    query = {}

    # Match any selected filters, case-insensitive
    if conditions:
        query["condition"] = {"$in": [re.compile(cond, re.IGNORECASE) for cond in conditions]} 
        
    if formats:
        query["format"] = {"$in": [re.compile(form, re.IGNORECASE) for form in formats]} 

    # if editions:
    #     query["edition"] = {"$in":[re.compile(ed, re.IGNORECASE) for ed in editions]}  
    edition_query = []
    for edition_range in editions:
        if edition_range == "1-5":
            edition_query.append({"edition": {"$regex": "^[1-5]"}})
        elif edition_range == "6-10":
            edition_query.append({"edition": {"$regex": "^[6-9]|10"}})
        elif edition_range == ">10":
            edition_query.append({"edition": {"$regex": "^[1-9][0-9]"}})

    # Make sure books match atleast one of the above mentioned edition conditions
    if edition_query:
        query["$or"] = edition_query 

    # Retrieve filtered books
    books = list(db.books.find(query))
# -------------------------------------------------------SORTING---------------------------------------------------
    sort_field = None
    sort_order = 1  # 1 = Ascending, -1 = Descending

    if sort_by == "price-high":
        sort_field = "price"
        sort_order = -1  
    elif sort_by == "price-low":
        sort_field = "price"
        sort_order = 1  
    elif sort_by == "year":
        sort_field = "year"
        sort_order = 1  

    # Fetch and sort books directly in MongoDB
    if sort_field:
        books = list(db.books.find(query).sort(sort_field, sort_order))
    else:
        books = list(db.books.find(query)) 

    return render_template("index.html", books=books)

# ----------------------------------------------------USER Profile-------------------------------------------------------

@app.route("/profile-page")
def user_profile():
    # Retrieve the user data from the database
    user_data = mongo.db.users.find_one({"_id": ObjectId(current_user.id)})
    listed_books = list(mongo.db.books.find({"_id": {"$in": user_data.get("listed_books", [])}}))

    return render_template("profile.html", user=current_user, listed_books=listed_books)

@app.route("/seller-profile/<seller_id>")
def seller_profile(seller_id):
    """
    Route to display the seller's profile and their book listings.
    """
    # Retrieve seller data from the database
    seller = db.users.find_one({"_id": ObjectId(seller_id)})

    if not seller:
        flash("Seller not found!", "danger")
        return redirect(url_for("home"))

    # Fetch books listed by the seller
    available_books = list(db.books.find({"seller_id": seller_id, "status": "Available"}))
    sold_books = list(db.books.find({"seller_id": seller_id, "status": "Sold"}))

    return render_template("seller_profile.html", seller=seller, available_books=available_books, sold_books=sold_books)
    
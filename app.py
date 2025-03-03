from flask import Flask, jsonify, request, render_template, request, redirect, url_for
from pymongo import MongoClient
import os
from dotenv import load_dotenv, dotenv_values
from bson.objectid import ObjectId
import re

# Load environment variables

load_dotenv()

def create_app():
    """
    Create and configure the Flask application.
    Returns: app: the Flask application object
    """
    app = Flask(__name__)

    # Load Flask config from .env variables
    config = dotenv_values()
    app.config.from_mapping(config)

    # Connect to MongoDB
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("MONGO_DBNAME")]
    # books_collection = db["books"]

    # Testing 
    print("Collections:", db.list_collection_names())
    print("Books:", list(db["books"].find({}).limit(5)))

    try:
        client.admin.command("ping")
        print("* Connected to MongoDB!")
    except Exception as e:
        print("* MongoDB connection error:", e)

    # Routes

    @app.route("/")
    def home():
        """
        Route for the home page.
        Returns: Rendered template (str): The rendered HTML template.
        """
        books = list(db["books"].find({}))  
        return render_template("index.html", books=books)

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
            }
            
            db.books.insert_one(new_book)

            return redirect(url_for("home"))
        return render_template("add_book.html")

    @app.route("/book/<book_id>")
    def book_details(book_id):
        """
        Route to display the details of a selected book.
        """
        book = db.books.find_one({"_id": ObjectId(book_id)})
        
        if not book:
            return "Book not found", 404

        return render_template("book_details.html", book=book)

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

    return app

# Run the Flask app
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)


import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

# ------------------------------------------------------------ Config MongoDB #
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


# ------------------------------------------------------------ Places #
@app.route("/")
@app.route("/get_places")
def get_places():
    places = list(mongo.db.places.find())
    return render_template("places.html", places=places)


# ------------------------------------------------------------ Search Index #
@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    places = list(mongo.db.places.find({"$text": {"$search": query}}))
    return render_template("places.html", places=places)


# ------------------------------------------------------------ Sign Up #
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("user"):
        return render_template("404.html")

    if request.method == "POST":
        # Check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("signup"))

        # Sign up new user in db
        signup = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(signup)

        # Put the new user into 'session'cookie
        session["user"] = request.form.get("username").lower()
        flash("You've Succesfully Signed Up!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("signup.html")


# ------------------------------------------------------------ Sign In #
@app.route("/signin", methods=["GET", "POST"])
def signin():
    # Only users that haven't signed in or up can access
    if session.get("user"):
        return render_template("404.html")

    if request.method == "POST":
        # Check if user exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # Ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "profile", username=session["user"]))
            else:
                # Invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("signin"))

        else:
            # Username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("signin"))

    return render_template("signin.html")


# ------------------------------------------------------------ Profile #
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # Only users can access
    if not session.get("user"):
        return render_template("404.html")

    # Grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        # Admin has access to all places
        if session["user"] == "admin":
            user_places = list(mongo.db.places.find())
        else:
            # User sees own places
            user_places = list(
                mongo.db.places.find({"created_by": session["user"]}))
        return render_template(
            "profile.html", username=username, user_places=user_places)

    return redirect(url_for("signin"))


# ------------------------------------------------------------ Sign Out #
@app.route("/signout")
def signout():
    # Remove user form session cookies
    if not session.get("user"):
        return render_template("404.html")

    flash("You have been signed out")
    session.pop("user")
    return redirect(url_for("signin"))


# ------------------------------------------------------------ Add Place #
@app.route("/add_place", methods=["GET", "POST"])
def add_place():
    # Only users can add places
    if not session.get("user"):
        return render_template("404.html")

    # Adding place to db
    if request.method == "POST":
        place = {
            "place_name": request.form.get("place_name"),
            "city": request.form.get("city"),
            "country": request.form.get("country"),
            "continent_name": request.form.get("continent_name"),
            "description": request.form.get("description"),
            "place_url": request.form.get("place_url"),
            "created_by": session["user"]
        }
        mongo.db.places.insert_one(place)
        flash("Place Succesfully Added")
        return redirect(url_for("get_places"))

    # Find continents from db
    continents = mongo.db.continents.find().sort("continent_name", 1)
    return render_template("add_place.html", continents=continents)


# ------------------------------------------------------------ Edit Place #
@app.route("/edit_place/<place_id>", methods=["GET", "POST"])
def edit_place(place_id):
    # Only users can edit places
    if not session.get("user"):
        return render_template("404.html")

    # Edit place in db
    if request.method == "POST":
        submit = {
            "place_name": request.form.get("place_name"),
            "city": request.form.get("city"),
            "country": request.form.get("country"),
            "continent_name": request.form.get("continent_name"),
            "description": request.form.get("description"),
            "place_url": request.form.get("place_url"),
            "created_by": session["user"]
        }
        mongo.db.places.update({"_id": ObjectId(place_id)}, submit)
        flash("Place Succesfully Updated")

    place = mongo.db.places.find_one({"_id": ObjectId(place_id)})
    continents = mongo.db.continents.find().sort("continent_name", 1)
    return render_template(
        "edit_place.html", place=place, continents=continents)


# ------------------------------------------------------------ Delete Place #
@app.route("/delete_place/<place_id>")
def delete_place(place_id):
    if not session.get("user"):
        return render_template("404.html")

    mongo.db.places.remove({"_id": ObjectId(place_id)})
    flash("Place Succesfully Deleted")
    return redirect(url_for("get_places"))


# ------------------------------------------------------------ Error Handler #
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


# ------------------------------------------------------------ Run The App #
if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)

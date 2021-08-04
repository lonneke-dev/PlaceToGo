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

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_places")
def get_places():
    places = list(mongo.db.places.find())
    return render_template("places.html", places=places)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    places = list(mongo.db.places.find({"$text": {"$search": query}}))
    return render_template("places.html", places=places)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("signup"))

        signup = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(signup)

        session["user"] = request.form.get("username").lower()
        flash("Registration Succesfull")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("signup.html")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                        request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                flash("Incorrect Username and/or Password")
                return redirect(url_for("signin"))

        else:
            flash("Incorrect Username and/or Password")
            return redirect(url_for("signin"))

    return render_template("signin.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("signin"))


@app.route("/signout")
def signout():
    flash("You have been signed out")
    session.pop("user")
    return redirect(url_for("signin"))


@app.route("/add_place", methods=["GET", "POST"])
def add_place():
    if request.method == "POST":
        place = {
            "place_name": request.form.get("place_name"),
            "city": request.form.get("city"),
            "country": request.form.get("country"),
            "continent_name": request.form.get("continent_name"),
            "description": request.form.get("description"),
            "created_by": session["user"]
        }
        mongo.db.places.insert_one(place)
        flash("Place Succesfully Added")
        return redirect(url_for("get_places"))

    continents = mongo.db.continents.find().sort("continent_name", 1)
    return render_template("add_place.html", continents=continents)


@app.route("/edit_place/<place_id>", methods=["GET", "POST"])
def edit_place(place_id):
    if request.method == "POST":
        submit = {
            "place_name": request.form.get("place_name"),
            "city": request.form.get("city"),
            "country": request.form.get("country"),
            "continent_name": request.form.get("continent_name"),
            "description": request.form.get("description"),
            "created_by": session["user"]
        }
        mongo.db.places.update({"_id": ObjectId(place_id)}, submit)
        flash("Place Succesfully Updated")

    place = mongo.db.places.find_one({"_id": ObjectId(place_id)})
    continents = mongo.db.continents.find().sort("continent_name", 1)
    return render_template(
        "edit_place.html", place=place, continents=continents)


@app.route("/delete_place/<place_id>")
def delete_place(place_id):
    mongo.db.places.remove({"_id": ObjectId(place_id)})
    flash("Place Succesfully Deleted")
    return redirect(url_for("get_places"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)

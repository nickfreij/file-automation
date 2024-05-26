import openai
import os
import json
import requests

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from urllib.parse import quote, unquote
from datetime import date

from helpers import login_required, apology

# Configure application
app = Flask(__name__)

# app secret key for flash messages so it can be stored in the session
app.config.update(SECRET_KEY=os.urandom(24))

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Import SQL Database into web app
db = SQL("sqlite:///database.db")

# Import API keys from config file
with open("config.json") as config_file:
    config = json.load(config_file)
    openai.api_key = config.get('openai', {}).get('api_key')
    usda_api_key = config.get('usda', {}).get('api_key')



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def home():
    "Homepage"
    if request.method == "GET":
        return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    "Register the user"

    if request.method == "POST":

        #make executable for full users list
        users = db.execute("SELECT * FROM users")

        #username checking
        if not request.form.get("username"):
            return apology("must provide username", 403)

        #password checking
        if not request.form.get("password"):
            return apology("must provide password", 403)

        #confirmation checking
        if not request.form.get("confirmation"):
            return apology("must provide confirmation", 403)

        elif (request.form.get("confirmation") != request.form.get("password")):
            return apology("must match passwords", 403)

        username = request.form.get("username")
        user_check = db.execute("SELECT username FROM users WHERE username = ?", username)

        if user_check:
            return apology("username already in use", 403)
        else:
            #generate hash
            password = request.form.get("password")
            password = generate_password_hash(password)

            #get height and weight
            height = request.form.get("height")
            height_unit = request.form.get("height_unit")
            weight = request.form.get("weight")
            weight_unit = request.form.get("weight_unit")

            #check if units are correct, then add to users
            if height_unit != ("in" or "cm"):
                return apology("incorrect unit use", 403)
            else:
                if weight_unit != ("lbs" or "kg"):
                    return apology("incorrect unit use", 403)
                else:
                    db.execute("INSERT INTO users (username, hash, height, weight, height_unit, weight_unit) VALUES (?, ?, ?, ?, ?, ?)", username, password, height, weight, height_unit, weight_unit)
                    return render_template("home.html")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if session:
        # Forget any current user id
        session.clear()

    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        user_db = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(user_db) != 1 or not check_password_hash(user_db[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["userid"] = user_db[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/supplement", methods = ["GET", "POST"])
@login_required
def supplement():
    """make a prompt for the user to type in a supplement"""
    if request.method == "GET":
        return render_template("supplement.html")


    if request.method == "POST":
        supp = request.form.get("supp")

        #chat gpt prompt
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"If {supp} is an real supplement, can you please show me all studies on the supplement called {supp} as it pertains to health and fitness and please give me the details on what they found? Please give it to me in 3 sentences max for each study and please do not make anything up, this needs to be 100% factual, I only want an answer on the studies so that the 3 sentences are not wasted, thank you",
            temperature=0,
            max_tokens=200,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0.1
            )
        return render_template("supplement.html", gptresponse = response)



@app.route("/aitrainer", methods = ["GET", "POST"])
@login_required
def aitrainer():
    """make a prompt for the user to type in questions for the ai trainer"""
    if request.method == "GET":
        return render_template("aitrainer.html")


    if request.method == "POST":

        aiquestion = request.form.get("aiquestion")

        if aiquestion:
            #chat gpt prompt
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=f"You are my AI personal trainer, here's my question: {aiquestion}.  Please do not add this prompt to your response.  Make the answer very detailed and step by step",
                temperature=0.2,
                max_tokens=3500,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0.6
                )
            return render_template("aitrainer.html", gptresponse = response)



@app.route("/nutrition", methods = ["GET", "POST"])
@login_required
def nutrition():
    """users to access nutrition page"""
    if request.method == "GET":
        #get the meal foods for today, user can select the date to change from html client side
        Meal_foods = db.execute("SELECT * FROM foodstorage WHERE id = ? AND date = ?", session["userid"], date.today())
        #get meal numbers to enter in the table
        Meal_numbers = db.execute("SELECT DISTINCT meal_id FROM foodstorage WHERE id = ? AND date = ? ORDER BY meal_id ASC", session["userid"], date.today())
        Meal_date = date.today()
        #create variable to store the dates so that the user can check
        Food_dates = db.execute("SELECT DISTINCT date FROM foodstorage WHERE id = ? ORDER BY date DESC", session["userid"])
        #make it to where if no meal foods for today, get the most recent day or at least show the option to change date
        #this if statement if no food has been added yet
        if Food_dates:
            if not Meal_foods:
                Meal_foods = db.execute("SELECT * FROM foodstorage WHERE id = ? AND date = ?", session["userid"], Food_dates[0]["date"])
                Meal_numbers = db.execute("SELECT DISTINCT meal_id FROM foodstorage WHERE id = ? AND date = ? ORDER BY meal_id ASC", session["userid"], Food_dates[0]["date"])
                Meal_date = Food_dates[0]["date"]
            #calculations on each meal, basically find all the foods for the user, the date, and each Meal_number, put in a list
            Meal_stats = []
            for Meal_number in Meal_numbers:
                #reset values
                totalcal = 0
                totalpro = 0
                totalcarbs = 0
                totalfats = 0
                totalsugars = 0
                totalfiber = 0

                #get the specific meals to add
                Meal_datas = db.execute("SELECT * FROM foodstorage WHERE id = ? AND date = ? AND meal_id = ?", session["userid"], Meal_date, Meal_number["meal_id"])
                #get the serving size to multiply to the 1 serving size amount
                #for loop to add all info
                for Meal_data in Meal_datas:
                    #just in case one of these values is 'None'
                    if Meal_data["calories"] != "None":
                        totalcal = totalcal + float(Meal_data["calories"])
                    if Meal_data["protein"] != "None":
                        totalpro = totalpro + float(Meal_data["protein"])
                    if Meal_data["carbs"] != "None":
                        totalcarbs = totalcarbs + float(Meal_data["carbs"])
                    if Meal_data["fats"] != "None":
                        totalfats = totalfats + float(Meal_data["fats"])
                    if Meal_data["sugars"] != "None":
                        totalsugars = totalsugars + float(Meal_data["sugars"])
                    if Meal_data["fiber"] != "None":
                        totalfiber = totalfiber + float(Meal_data["fiber"])
                #after all added, appenc for themeal number so we can display it in html
                Meal_stats.append({
                "mealid" : Meal_number["meal_id"],
                "totalcal" : totalcal,
                "totalpro" : totalpro,
                "totalcarbs" : totalcarbs,
                "totalfats" : totalfats,
                "totalsugars" : totalsugars,
                "totalfiber" : totalfiber
                })
        return render_template("nutrition.html", meal_foods=Meal_foods, food_dates=Food_dates, meal_numbers=Meal_numbers, meal_stats = Meal_stats)

    """users pick the food they want to add to their meal"""
    if request.method == "POST":
        #radio has to be selected
        if request.form.get("radiofoodadd"):
            #positive serving
            if float(request.form.get("servingsizeamt")) > 0:
                brand_add = request.form.get("brandname")
                # brings foodname from website format to normal format
                food_add = unquote(request.form.get("foodname"))
                #for serving_add we do addition for the serving and then add the measurement
                serving_size = request.form.get("servingsize")
                ssunit = request.form.get("ssunit")
                serving_add_calc = float(serving_size) * float(request.form.get("servingsizeamt"))
                ssize = float(request.form.get("servingsizeamt"))
                serving_add = str(serving_add_calc) + " " + ssunit
                cal_add = float(request.form.get("calories")) * ssize
                pro_add = float(request.form.get("protein")) * ssize
                carbs_add = float(request.form.get("carbs")) * ssize
                fats_add = float(request.form.get("fats")) * ssize
                if request.form.get("sugars") != "None":
                    sugars_add = float(request.form.get("sugars")) * ssize
                else:
                    sugars_add = 0
                if request.form.get("fiber") != "None":
                    fiber_add = float(request.form.get("fiber")) * ssize
                else:
                    fiber_add = 0
                date_add = date.today()
                meal_id = request.form.get("mealid")

                db.execute("INSERT into foodstorage (id, foodname, brandname, servingsize, calories, protein, carbs, fats, sugars, fiber, meal_id, date, servingamt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", session["userid"], food_add, brand_add, serving_add, cal_add, pro_add, carbs_add, fats_add, sugars_add, fiber_add, meal_id, date_add, request.form.get("servingsizeamt"))

                return redirect("/nutrition")
            else:
                return apology("Sorry bro, you can't have negative food", 403)
        else:
            return apology("Sorry bro, you didn't select a food", 403)



# function to call when you search for each parameter in the food, finding the food
# goes through the nested "foodNutrients" in order to find the matching id that is in the variable nutrient_id
def nutrientid_search(food, nutrient_id):
    foodnutrients = food.get("foodNutrients", [{}])
    for foodnutrient in foodnutrients:
        if foodnutrient.get("nutrientId") == nutrient_id:
            return foodnutrient.get("value")
    return(None)


@app.route("/nutrition/foodsearch", methods = ["GET"])
def nutrition_foodsearch():
    """let users search for food"""
    if request.method == "GET":
        if request.args.get("food"):
            food_search = request.args.get("food")
            #make into a string for websites 80% certain
            encoded_food = quote(food_search)
            #request the food using requests
            rqstfood = requests.get(f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={usda_api_key}&query={encoded_food}")
            if rqstfood.status_code == 200:
                jsonfoodsearch = rqstfood.json() #puts request into a json object
                foods = jsonfoodsearch.get("foods", [])
                if foods:
                    nutrient_data = []
                    for food in foods:
                        # take out foods with no names
                        if food.get("brandName") != None:
                            nutrient_data.append({
                            "Brandname": food.get("brandName"),
                            "Foodname": unquote(encoded_food),
                            "Servingsize": f"{food.get('servingSize')} {food.get('servingSizeUnit')}",
                            "ssunit": food.get('servingSizeUnit'),
                            "Calories": nutrientid_search(food,1008),
                            "Protein": nutrientid_search(food,1003),
                            "Carbohydrates": nutrientid_search(food,1005),
                            "Fats": nutrientid_search(food,1004),
                            "Sugars": nutrientid_search(food,2000),
                            "Fiber": nutrientid_search(food,1079)
                            })
                else:
                    flash('Something went wrong.')
            else:
                flash(f'{food_search} not found, please try again','error')

           # return redirect(url_for("nutrition_foodsearch")) I don't need this added, thought I did

    return render_template("nutrition.html", nutrients = nutrient_data, foodsearched = food_search)

@app.route("/datechange", methods = ["POST"])
@login_required
def datechange():
    #When someone chooses new date, fill the table in nutrition.html w corresponding data from that date
    if request.method == "POST":
        date_change = request.form.get("datechange")
        date_pull = db.execute("SELECT * FROM foodstorage WHERE id = ? AND date = ?", session["userid"], date_change)
        #Repeated from nutrition.html so that the dates get pulled back after a switch in dates
        Food_dates = db.execute("SELECT DISTINCT date FROM foodstorage WHERE id = ? ORDER BY date DESC", session["userid"])
        # Food_dates = db.execute("SELECT DISTINCT date FROM foodstorage WHERE id = ? AND date <> ? ORDER BY date DESC", session["userid"], date_change)

        Meal_numbers = db.execute("SELECT DISTINCT meal_id FROM foodstorage WHERE id = ? AND date = ? ORDER BY meal_id ASC", session["userid"], date_change)

        Meal_stats = []
        for Meal_number in Meal_numbers:
            #reset values
            totalcal = 0
            totalpro = 0
            totalcarbs = 0
            totalfats = 0
            totalsugars = 0
            totalfiber = 0

            #get the specific meals to add
            Meal_datas = db.execute("SELECT * FROM foodstorage WHERE id = ? AND date = ? AND meal_id = ?", session["userid"], date_change, Meal_number["meal_id"])
            #get the serving size to multiply to the 1 serving size amount
            #for loop to add all info
            for Meal_data in Meal_datas:
                #just in case one of these values is 'None'
                if Meal_data["calories"] != "None":
                    totalcal = totalcal + float(Meal_data["calories"])
                if Meal_data["protein"] != "None":
                    totalpro = totalpro + float(Meal_data["protein"])
                if Meal_data["carbs"] != "None":
                    totalcarbs = totalcarbs + float(Meal_data["carbs"])
                if Meal_data["fats"] != "None":
                    totalfats = totalfats + float(Meal_data["fats"])
                if Meal_data["sugars"] != "None":
                    totalsugars = totalsugars + float(Meal_data["sugars"])
                if Meal_data["fiber"] != "None":
                    totalfiber = totalfiber + float(Meal_data["fiber"])
            #after all added, appenc for themeal number so we can display it in html
            Meal_stats.append({
            "mealid" : Meal_number["meal_id"],
            "totalcal" : totalcal,
            "totalpro" : totalpro,
            "totalcarbs" : totalcarbs,
            "totalfats" : totalfats,
            "totalsugars" : totalsugars,
            "totalfiber" : totalfiber
            })
        return render_template("nutrition.html", meal_foods = date_pull, food_dates = Food_dates, thedate = date_change, meal_numbers=Meal_numbers, meal_stats = Meal_stats)

@app.route("/account", methods = ["GET", "POST"])
@login_required
def account():
    "Account"
    if request.method == "GET":

        acct_info = db.execute("SELECT * FROM users WHERE id = ?", session["userid"])
        return render_template("account.html", acct_info=acct_info)

    if request.method == "POST":
        #after requesting that you want a change, a button will appear to submit which will be post via account route
        #changing weight and height
        if request.form.get("height"):
            height_change = request.form.get("height")
            height_unit = request.form.get("height_unit")
            db.execute("UPDATE users SET height = ?,height_unit = ? WHERE id = ?",height_change,height_unit,session["userid"])
        if request.form.get("weight"):
            weight_change = request.form.get("weight")
            weight_unit = request.form.get("weight_unit")
            db.execute("UPDATE users SET weight = ?,weight_unit = ? WHERE id = ?",weight_change,weight_unit,session["userid"])
        #changing password
        if request.form.get("newpw1") and request.form.get("newpw2") and request.form.get("currentpw"):
            actualcurrentpw = db.execute("SELECT hash FROM users WHERE id = ?",session["userid"])

            if not request.form.get("newpw1") == request.form.get("newpw2"):
                return apology("passwords don't match", 403)
            elif not check_password_hash(actualcurrentpw[0]["hash"],request.form.get("currentpw")):
                return apology("current password incorrect", 403)
            else:
                newpw = request.form.get("newpw1")
                db.execute("UPDATE users SET hash = ? WHERE id = ?",hash(newpw),session["userid"])

        acct_info = db.execute("SELECT * FROM users WHERE id = ?", session["userid"])
        return render_template("account.html", acct_info=acct_info)

@app.route("/accountchange", methods = ["GET"])
@login_required
def accountchange():
    "Change account info"
    if request.method == "GET":
      #arbitrary number just so that change_request exists and the forms pop up in account.html with the if statement
      change_request = 1
      return render_template("account.html", change_request = change_request)

@app.route("/accountpassword", methods = ["GET"])
@login_required
def accountpassword():
    "Change account password"
    if request.method == "GET":
      #arbitrary number just so that change_request exists and the forms pop up in account.html with the if statement
      change_password = 1
      return render_template("account.html", change_password = change_password)

#run the app directly, never really used in this project's case
if __name__ == '__main__':
    app.run(debug=False)
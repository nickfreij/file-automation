# sirnickGetFit Fitness Web Application
#### Video Demo: https://youtu.be/lC_-vUuiwM8
#### Description:
This fitness website give you access to the following: creating an accountchanging your height, weight, or password after creating an account, access the power of Chat GPT to ask questions on supplements, use Chat GPT to also act as your personal AI trainer, search for foods and log your nutrition into the website under meals to track progress

In the static folder, all of the backgrounds for each page is stored, including the video in the home screen, labeled kevin.mp4. Additionally, the dumbbell picture, which is the icon on the website tab, is stored here.  Lastly, the apikey.txt is also stored.  This is a txt file for the purpose of remembering what the Chat GPT API key is.

In the templates folder, we have an html for each page: account (for changing account info), aitrainer (for displaying the AI trainer input and output), apology (for the case of making a mistake), home, layout, login, nutrition (nutrition log), register, and supplement (for input and output of Chat GPT).  Each are different, some I used Javascript to do certain things, such as a pause play button in home, or an alert when a meal is added in nutrition.  In nutrition, I also used javascript to make sure no extra dates showed up on the drag down menu where you decide what date to pull nutrition info from.

The config.json file gets imported into app.py and essentially stores the API keys with added security.  I have a requirements.txt file to show what the program needs, and I used the apology & login-required from helpers.py from the Finance project.

I have two databases in SQL, one for the users, and the other for the food, called foodstorage, which is linked to users via a primary key id.

One big thing to note in the app.py is that for nutrition.html, I use the view functions nutrition (for pulling nutrition.html and adding food into the SQL database), nutrition_foodsearch (which displays the json output from searching a food and accessing the database from the USDA API), datechange (for changing the date and displaying the food), and the function nutritionid_search (which is used in nutrition_foodsearch to pull the macronutrients much more efficiently).

I debated whether I should make more html templates or find a way to incorporate multiple get and post requests in a single html template.  The latter is what I did, and I do so by using jinja and making if statements so that certain things would appear only when I need them to.  It took me a very long time to implement the USDA API, I ended up finding out that the info on the foods you can search isn't very detailed but I decided to stick with this API because it was free and still did the job.

I have a venv folder for all the plugins for my project. Please make sure to activate the virtual environment before doing flask run in order to run the code:   source bin/venv/activate


I used Github Desktop in order to add the venv folder as well as some big files that couldn't be zipped.  It caused my gradebook to read 10/11 completed even though last submission it showed 11/11.  I am resubmitting and hoping it goes through, hence the changes to the README here. Thank you for reading, and thank you for this course!!!
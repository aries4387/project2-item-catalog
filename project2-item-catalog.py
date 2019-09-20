import os


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.exceptions import HTTPException, default_exceptions

from database_setup import Base, Category, Item, User
from flask import session as login_session

import json
import requests

from flask import (Flask, render_template, request, redirect, url_for, jsonify)

from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configuration
# GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_ID = "72634954769-a83u9pdi2kuhn9qqdrslju70r0qpm1uh.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "g_RHm9D4nmUH3tCAqwSg09a9"
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# OAuth2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route('/login')
def showLogin():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in our db with the information provided
    # by Google
    user = User(
        id=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add to database
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("viewCategories"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("viewCategories"))


@app.route('/categories/JSON')
def categoriesJSON():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    categories = session.query(Category).all()
    return jsonify(Category=[c.serialize for c in categories])


@app.route('/categories/<int:category_id>/items/JSON')
def categoryItemsJSON(category_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/categories/<int:category_id>/items/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    item = session.query(Item).filter_by(id=item_id).first()
    return jsonify(Item=item.serialize)


@app.route('/')
@app.route('/categories')
def viewCategories():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    
    categories = session.query(Category).all()
    allitems = session.query(Item).all()
    currentUserID = current_user.get_id()

    result = {}

    for category in categories:
        categoryItems = session.query(Item).filter(Item.category_id == category.id).all()
        result[category.name] = categoryItems
    items = session.query(Item).order_by(Item.id.desc())
    if 'username' not in login_session:
        return render_template('publiccategories.html', categories=categories, items=items, result=result,
                               userid=currentUserID)
    else:
        return render_template('category.html', categories=categories, items=items)


@app.route('/categories/add', methods=['GET', 'POST'])
def addCategory():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCategory)
        session.commit()
        return redirect(url_for('viewCategories'))
    else:
        return render_template('newcategory.html')


@app.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedCategory.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this category. Please create your own category in order to edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
        session.add(editedCategory)
        session.commit()
        return redirect(url_for('viewCategories'))
    else:
        return render_template('editcategory.html', category=editedCategory)


@app.route('/categories/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if categoryToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this restaurant. Please create your own restaurant in order to delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        return redirect(url_for('viewCategories', category_id=category_id))
    else:
        return render_template('deletecategory.html', category=categoryToDelete)


@app.route('/categories/<int:category_id>')
@app.route('/categories/<int:category_id>/items')
def viewItems(category_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    if 'username' not in login_session:
        return render_template('publiccatitem.html', category=category, items=items, category_id=category.id)
    else:
        return render_template('categoryitems.html', category=category, items=items, category_id=category.id)


@app.route('/categories/<int:category_id>/items/<int:item_id>')
def viewItem(category_id, item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    clickedItem = session.query(Item).filter_by(id=item_id).one()
    if 'username' not in login_session:
        return render_template('publicitem.html', category_id=category_id, item_id=item_id, item=clickedItem)
    else:
        return render_template('item.html', category_id=category_id, item_id=item_id, item=clickedItem)


@app.route('/categories/<int:category_id>/add', methods=['GET', 'POST'])
def addItem(category_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id=category_id).one()
    loggedinuser = current_user.get_id();
    if not current_user.is_authenticated:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Item(title=request.form['name'], description=request.form['description'], category_id=category_id,
                       user_id=loggedinuser)
        session.add(newItem)
        session.commit()
        return redirect(url_for('viewCategories'))
    else:
        return render_template('newitem.html', category_id=category_id)


@app.route('/categories/<int:category_id>/items/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    editedItem = session.query(Item).filter_by(id=item_id).one()
    currentUserID = current_user.get_id()

    if not current_user.is_authenticated:
        return redirect('/login')

    if request.method == 'POST':
        if request.form['title']:
            editedItem.title = request.form['title']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('viewCategories'))
    else:
        return render_template('edititem.html', category_id=category_id, item_id=item_id, item=editedItem)


@app.route('/categories/<int:category_id>/items/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id=category_id).one()
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    currentUserID = current_user.get_id()
    if not current_user.is_authenticated:
        return redirect('/login')

    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('viewCategories'))
    else:
        return render_template('deleteitem.html', item=itemToDelete)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


def handle_error(error):
    code = 500
    if isinstance(error, HTTPException):
        code = error.code
    return jsonify(error='error', code=code)


for exc in default_exceptions:
    app.register_error_handler(exc, handle_error)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)

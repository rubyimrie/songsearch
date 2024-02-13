from flask import Flask, url_for, request, render_template, redirect, url_for
from markupsafe import escape

app = Flask(__name__)

from flask import url_for


users = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = None

    if request.method == 'POST':
        # Retrieve the search query from the form
        search_query = request.form.get('search_query')

    return render_template('search.html', search_query=search_query)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            return redirect(url_for('profile', username=username))
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return render_template('signup.html', error="Username already exists")
        else:
            users[username] = password
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/profile/<username>')
def profile(username):
    return render_template('profile.html', username=username)


from flask import Flask, url_for, request, render_template, redirect, url_for
from markupsafe import escape

app = Flask(__name__)
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

@app.route('/search_results', methods=['POST'])
def search_results():
    search_query = request.form.get('search_query')
    # For simplicity, let's assume you have a list of search results
    # Replace this with your actual search logic
    search_results = [
        {"image": "https://i.scdn.co/image/ab67616d0000b2738863bc11d2aa12b54f5aeb36", "song_name": "Blinding Lights", "artist": "The Weeknd", "lyric_sentence": "Lyric sentence 1"},
        {"image": "https://i1.sndcdn.com/artworks-5VCxiNQdKysNTV2y-Qu5QwQ-t500x500.jpg", "song_name": "Someone you loved", "artist": "Lewis Capaldi", "lyric_sentence": "Lyric sentence 2"},
        {"image": "https://upload.wikimedia.org/wikipedia/en/b/b0/SoftCellTaintedLove7InchSingleCover.jpg", "song_name": "Tainted Love", "artist": "Soft Cell", "lyric_sentence": "Lyric sentence 3"}
    ]
    return render_template('search_results.html', search_query=search_query, search_results=search_results)

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

if __name__ == "__main__":
    app.run(debug=True)
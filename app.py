from flask import Flask, url_for, request, render_template, redirect, url_for, session
from markupsafe import escape
import requests


app = Flask(__name__)
users = {
    'user1': 'password1',
    'user2': 'password2',
    'user3': 'password3'
}
mock_playlists = {
            'user1': ['Playlist 1', 'Playlist 2', 'Playlist 3'],
            'user2': ['Playlist A', 'Playlist B'],
            'user3': ['My Playlist', 'Favorites']
        }


import requests

@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = None
    search_results = []
    error_message = None

    if request.method == 'POST':
        # Retrieve the search query from the form
        search_query = request.form.get('search_query')

        # Make a GET request to the API endpoint for searching
        api_url = 'http://34.82.129.217:5000/ranked'
        params = {'query': search_query, 'page': 2, 'filter': '', 'ranking': '1', 'show': 0}  # Adjust parameters as needed
        response = requests.get(api_url, params=params)
        
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            ranked_results = data[0]  # Extract the list of search results
            total_results = data[1]   # Extract the total number of results
            
            if ranked_results:
                # Format the search results for display
                for result in ranked_results:
                    search_results.append({
                        'song_name': result['title'],
                        'artist': result['artist'],
                        'id': result['id'],
                        'album': result['album'],
                        'released_year': result['released_year']
                    })
            else:
                error_message = f'No results found for the query: {search_query}'
        else:
            # Handle error response
            error_message = f'Error: {response.status_code} - An error occurred while searching.'

    # Render the index page template
    return render_template('search.html', search_query=search_query, search_results=search_results, error=error_message)



@app.route('/song_details/<id>')
def song_details(id):
    # Make a GET request to the API endpoint for retrieving song details
    api_url = f'http://34.82.129.217:5000/song_by_id?id={id}'
    response = requests.get(api_url)
    
    if response.status_code == 200:
        # Parse the JSON response
        song_details = response.json()
        return render_template('song_details.html', song=song_details)
    else:
        # Handle error response
        return render_template('error.html', error='An error occurred while retrieving song details.')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            # Set the user in the session upon successful login
            session['user'] = username
            playlists = mock_playlists.get(username, [])
            return redirect(url_for('profile', username=username, playlists=playlists))
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

# Logout route
@app.route('/logout')
def logout():
    # Remove user session
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    # Check if user is logged in
    if 'user' in session:
        username = session['user']
        
        # Mock playlists for each user
        mock_playlists = {
            'user1': ['Playlist 1', 'Playlist 2', 'Playlist 3'],
            'user2': ['Playlist A', 'Playlist B'],
            'user3': ['My Playlist', 'Favorites']
        }
        
        # Retrieve playlists for the current user
        playlists = mock_playlists.get(username, [])
        
        return render_template('profile.html', username=username, playlists=playlists)
    else:
        # If user is not logged in, redirect to login page
        return redirect(url_for('login'))
    


if __name__ == "__main__":
    app.run(debug=True)

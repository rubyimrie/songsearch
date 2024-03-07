from flask import Flask, url_for, request, render_template, redirect, url_for, session, flash
from markupsafe import escape
import requests


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management


@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = None
    search_type = 'ranked'
    search_results = []
    error_message = None

    if request.method == 'POST':
        # Retrieve the search query and type from the form
        search_query = request.form.get('search_query')
        search_type = request.form.get('search_type')

        # Prepare parameters for API request based on search type
        if search_type == 'ranked':
            ranking = request.form.get('ranking')
            params = {'query': search_query, 'page': 1, 'filter': '', 'ranking': ranking, 'show': 0}  # Adjust common parameters as needed
            api_url = 'http://34.82.129.217:5000/ranked'
            type = None
        elif search_type == 'simple':
            type = request.form.get('search_option')
            if type == '2':
                prox = request.form.get('proximity')
            else:
                prox = 0
            params = {'query': search_query, 'page': 1, 'filter': '', 'type':type, 'show': 0, 'proximity':prox}  # Adjust common parameters as needed
            api_url = 'http://34.82.129.217:5000/search'
        
        # Make a GET request to the appropriate API endpoint
        response = requests.get(api_url, params=params)
        
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            search_results = data[0]  # Assuming the response contains the search results directly
            
            if not search_results:
                error_message = f'No results found for the query: {search_query}'
        else:
            # Handle error response
            error_message = f'Error: {response.status_code} - An error occurred while searching.'

    # Retrieve liked song IDs
    liked_songs_response = requests.get('http://34.82.129.217:5000/LikedSongs', json={'email': session.get('user')})
    liked_song_ids = [song['id'] for song in liked_songs_response.json()]

    # Render the index page template
    return render_template('search.html', search_query=search_query, search_type=search_type, search_results=search_results, liked_song_ids=liked_song_ids, error=error_message)





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
    error_message = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            error_message = 'Email or password is missing'
        else:
            api_url = 'http://34.82.129.217:5000/login'
            try:
                response = requests.post(api_url, json={'email': email, 'password': password})
                if response.status_code == 200:
                    # Store the user's email in the session upon successful login
                    session['user'] = email
                    return redirect(url_for('profile'))
                elif response.status_code == 401:
                    error_message = 'Invalid email or password'
                else:
                    error_message = 'An error occurred. Please try again later.'
            except requests.exceptions.RequestException as e:
                error_message = 'An error occurred during the request. Please try again later.'

    return render_template('login.html', error=error_message)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error_message = None

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Make a POST request to the API endpoint for signing up
        api_url = 'http://34.82.129.217:5000/signup'
        data = {'name': name, 'email': email, 'password': password}  
        response = requests.post(api_url, json=data)
        
        if response.status_code == 400:
            error_message = f'Email or password is missing'
        elif response.status_code == 409:
            error_message = f'User already exists'
        elif response.status_code == 200:
            # User signup was successful
            return redirect(url_for('login'))
            # error_message = f'Success'
        else:
            error_message = f'An error occurred'

    return render_template('signup.html', error=error_message)


# Logout route
@app.route('/logout', methods=['POST'])
def logout():
    # Make a POST request to the API endpoint for logout
    api_url = 'http://34.82.129.217:5000/logout'
    response = requests.post(api_url)
    
    # Check the response status code
    if response.status_code == 200:
        error_message = 'Logout successful'
    else:
        error_message = 'An error occurred'

    # Redirect to the login page with an error message
    return redirect(url_for('login'), error=error_message)

@app.route('/profile')
def profile():
    # Check if user is logged in
    if 'user' in session:
        email = session['user']
        
        api_url = 'http://34.82.129.217:5000/LikedSongs'  
        data = {'email': email}  
        response = requests.get(api_url, json=data)
        
        return render_template('profile.html', username=email, likedSongs=response.json()) 
    else:
        # If user is not logged in, redirect to login page
        return redirect(url_for('login'))
    
@app.route('/saveSong', methods=['POST'])
def saveSong():
    # Get the song ID and user email from the form
    song_id = request.form['song_id']
    email = session.get('user')  # Retrieve user email from the session
    
    if not email:
        # If user is not logged in, redirect to login page
        return redirect(url_for('login'))

    # Make a POST request to the API endpoint for liking a song
    api_url = 'http://34.82.129.217:5000/Like'
    data = {'id': song_id}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(api_url, json=data, headers=headers)
        if response.status_code == 200:
            # Song liked successfully
            return redirect(url_for('profile'))
        elif response.status_code == 409:
            # Song already liked by the user
            error_message = 'You have already liked this song.'
        else:
            error_message = 'An error occurred while liking the song.'
    except requests.exceptions.RequestException as e:
        error_message = 'An error occurred during the request. Please try again later.'

    # Render the profile page template with an error message
    username = session.get('user')
    likedSongs = requests.get('http://34.82.129.217:5000/LikedSongs', json={'email': email}).json()
    return render_template('profile.html', username=username, likedSongs=likedSongs, error=error_message)



@app.route('/deleteSong', methods=['POST'])
def deleteSong():
    # Get the song ID from the form
    song_id = request.form['song_id']
    email = session['user']  # Retrieve user email from the session
    
    # Make a POST request to the API endpoint
    api_url = 'http://34.82.129.217:5000/DeleteSong'
    data = {'email': email, 'id': song_id}  # Prepare the JSON data
    response = requests.post(api_url, json=data)
    
    if response.status_code == 200:
        error_message='Song deleted successfully!'
    else:
        error_message='An error occurred while deleting the song.'

    username = session.get('user')
    likedSongs = requests.get('http://34.82.129.217:5000/LikedSongs', json={'email': email}).json()
    return render_template('profile.html', username=username, likedSongs=likedSongs, error=error_message)

if __name__ == "__main__":
    app.run(debug=True)

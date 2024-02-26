from flask import Flask, url_for, request, render_template, redirect, url_for, session
from markupsafe import escape
from code_song_withAPI import get_ranked_queries, get_song


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


@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = None

    if request.method == 'POST':
        # Retrieve the search query from the form
        search_query = request.form.get('search_query')

        # Call the function to get ranked queries
        ranked_results, total_results = get_ranked_queries(search_query, '', 1, '1')

        if ranked_results is None:
            # Handle case where no results are found
            search_results = []
            error_message = 'No results found for the query: {}'.format(search_query)
        else:
            # Format the search results for display
            search_results = []
            for result in ranked_results:
                search_results.append({
                    'song_name': result['title'],
                    'artist': result['artist'],
                    'id': result['id']
                })
            error_message = None

        return render_template('search.html', search_query=search_query, search_results=search_results, error=error_message)

    # Render the index page template
    return render_template('search.html', search_query=search_query)

@app.route('/song_details/<id>')
def song_details(id):
    # Call the function to get the details of the song by its ID
    song = get_song(id)

    
    # Render the song details page template with the song details
    return render_template('song_details.html', song=song)

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
    
@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    # Check if user is logged in
    if 'user' in session:
        playlist_name = request.form.get('playlist_name')
        # Add code to save the new playlist to the database or wherever you store playlists
        # For example:
        # playlist = Playlist(name=playlist_name, user_id=session['user'])
        # db.session.add(playlist)
        # db.session.commit()
        # Assuming you're using SQLAlchemy and have a Playlist model
        
        # Redirect the user back to their profile page after creating the playlist
        return redirect(url_for('profile'))
    else:
        # If user is not logged in, redirect to login page
        return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
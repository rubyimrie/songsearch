from flask import Flask, url_for, request, render_template
from markupsafe import escape

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = None

    if request.method == 'POST':
        # Retrieve the search query from the form
        search_query = request.form.get('search_query')

    return render_template('search.html', search_query=search_query)


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

if __name__ == "__main__":
    app.run(debug=True)
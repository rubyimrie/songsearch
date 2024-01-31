from flask import Flask, url_for, request, render_template
from markupsafe import escape

app = Flask(__name__)

from flask import url_for



@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = None

    if request.method == 'POST':
        # Retrieve the search query from the form
        search_query = request.form.get('search_query')

    return render_template('search.html', search_query=search_query)




from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from form import FindMovieForm, RateMovieForm
import sqlite3
import requests

MOVIE_DB_API_KEY = "8a5a5c25b5796fc510b0aca7e18d25c9"
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

DB_PATH = "movies.db"

# Initialize database and create table
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE NOT NULL,
                year INTEGER NOT NULL,
                description TEXT NOT NULL,
                rating REAL,
                ranking INTEGER,
                review TEXT,
                img_url TEXT NOT NULL
            );
        ''')
        conn.commit()

init_db()


@app.route("/")
def home():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM movies ORDER BY rating DESC")
        all_movies = cursor.fetchall()
        for i, movie in enumerate(all_movies):
            movie_id = movie[0]
            ranking = len(all_movies) - i
            cursor.execute("UPDATE movies SET ranking = ? WHERE id = ?", (ranking, movie_id))
        conn.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = FindMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(MOVIE_DB_SEARCH_URL, params={
            "api_key": MOVIE_DB_API_KEY, "query": movie_title
        })
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={
            "api_key": MOVIE_DB_API_KEY, "language": "en-US"
        })
        data = response.json()
        new_movie = (
            data["title"],
            int(data["release_date"].split("-")[0]),
            data["overview"],
            None,
            None,
            None,
            f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}"
        )
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO movies (title, year, description, rating, ranking, review, img_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', new_movie)
            conn.commit()
        return redirect(url_for("home"))


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
        movie = cursor.fetchone()
    if form.validate_on_submit():
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE movies
                SET rating = ?, review = ?
                WHERE id = ?
            ''', (float(form.rating.data), form.review.data, movie_id))
            conn.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
        conn.commit()
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)
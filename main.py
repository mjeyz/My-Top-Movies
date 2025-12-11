from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from form import FindMovieForm, RateMovieForm
import requests
import mysql.connector
from mysql.connector import Error

MOVIE_DB_API_KEY = "8a5a5c25b5796fc510b0aca7e18d25c9"
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '9992',
    'database': 'my_top_movies'
}


def get_db_connection():
    """Helper function to get database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_db():
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS my_top_movies")
        cursor.close()
        conn.close()

        # Now create table
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS movies
                           (
                               id
                               INT
                               AUTO_INCREMENT
                               PRIMARY
                               KEY,
                               title
                               VARCHAR
                           (
                               255
                           ) UNIQUE NOT NULL,
                               year INT NOT NULL,
                               description TEXT NOT NULL,
                               rating DECIMAL
                           (
                               3,
                               1
                           ),
                               ranking INT,
                               review TEXT,
                               img_url TEXT NOT NULL
                               )
                           ''')
            conn.commit()
            cursor.close()
            conn.close()
            print("Database initialized successfully")
    except Error as e:
        print(f"Error initializing database: {e}")


init_db()


@app.route("/")
def home():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM movies ORDER BY rating DESC")
        all_movies = cursor.fetchall()

        # Update rankings
        for i, movie in enumerate(all_movies):
            movie_id = movie[0]
            ranking = len(all_movies) - i
            cursor.execute("UPDATE movies SET ranking = %s WHERE id = %s", (ranking, movie_id))

        conn.commit()
        cursor.close()
        conn.close()
        return render_template("index.html", movies=all_movies)
    return "Database connection error", 500


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

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                               INSERT
                               IGNORE INTO movies (title, year, description, rating, ranking, review, img_url)
                    VALUES (
                               %s,
                               %s,
                               %s,
                               %s,
                               %s,
                               %s,
                               %s
                               )
                               ''', new_movie)
                conn.commit()
            except Error as e:
                print(f"Error inserting movie: {e}")
            finally:
                cursor.close()
                conn.close()

        return redirect(url_for("home"))
    return redirect(url_for("add_movie"))


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM movies WHERE id = %s", (movie_id,))
        movie = cursor.fetchone()
        cursor.close()
        conn.close()
    else:
        return "Database connection error", 500

    if form.validate_on_submit():
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                           UPDATE movies
                           SET rating = %s,
                               review = %s
                           WHERE id = %s
                           ''', (float(form.rating.data), form.review.data, movie_id))
            conn.commit()
            cursor.close()
            conn.close()
        return redirect(url_for('home'))

    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM movies WHERE id = %s", (movie_id,))
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)
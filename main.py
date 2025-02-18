from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap5
import sqlite3
import os
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# Ensure instance directory exists
os.makedirs("instance", exist_ok=True)

# Database file path
db_path = "instance/movie.db"

# Create or connect to the database and initialize it
def initialize_db():
    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            year INTEGER,
            description TEXT,
            rating REAL,
            ranking INTEGER,
            review TEXT,
            img_url TEXT
        );
        ''')

        # Insert movie data if not already present
        try:
            cursor.execute('''
            INSERT OR IGNORE INTO movies (title, year, description, rating, ranking, review, img_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                "Phone Booth",
                2002,
                "Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. "
                "Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
                7.3,
                10,
                "My favourite character was the caller.",
                "https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
            ))

            cursor.execute('''
            INSERT OR IGNORE INTO movies (title, year, description, rating, ranking, review, img_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                "Avatar The Way of Water",
                2022,
                "Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, "
                "Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, "
                "the battles they fight to stay alive, and the tragedies they endure.",
                7.3,
                9,
                "I liked the water.",
                "https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
            ))
            db.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")


initialize_db()

@app.route("/")
def home():
    # Fetch all movies to display on the homepage
    with sqlite3.connect(db_path) as bd:
        cursor = bd.cursor()
        cursor.execute("SELECT * FROM movies")
        movies = cursor.fetchall()

    return render_template("index.html", movies=movies)

class MovieForm(FlaskForm):
    rating = FloatField("Your rating out of 10 e.g 7.5", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    button = SubmitField("Done")

@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = MovieForm()

    return render_template("edit.html", form=form)

if __name__ == '__main__':
    app.run(debug=True)

#!/usr/bin/python3
from flask import Flask, render_template
from flask_talisman import Talisman

app = Flask(__name__)
Talisman(app)


@app.route("/")
def homepage():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

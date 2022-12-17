#!/usr/bin/env python
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def homepage():
    return render_template("index.html")


@app.route("/blog/")
def blog():
    return render_template("blog.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

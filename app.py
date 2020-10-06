import json
import os

import requests
from urllib.parse import unquote
from flask import Flask, render_template, request, redirect
from flask_bootstrap import Bootstrap

# Get all the lovely prettyness
def create_app():
  app = Flask(__name__)
  Bootstrap(app)
  return app
app = create_app()

# Parse the activity into something useful
def get_activity():
    where_we_are = os.path.dirname(os.path.realpath(__file__))
    with open(where_we_are+"/parsed/22-9-2020.json", "r") as f:
      data = json.load(f)

    return data


# Endpoint for viewing cards that have moved
@app.route("/move", methods=["GET"])
def map_extend():
    return render_template("card-moves.html", data=get_activity())

if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template
from config import config
from models.db_models import db

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)

with app.app_context():
    db.create_all() #creates all tables if they don't exist

@app.route("/")
def index():
    return render_template('upload.html')


app.run(debug=True)
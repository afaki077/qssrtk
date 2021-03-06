# -*- coding: utf8 -*-

########################################################
#                                                      #
# Name       : Qssrtk                                  #
#                                                      #
# Description: A lightweight Url shortener script      # 
#                                                      #
# Developer  : Abdelhadi Dyouri                        # 
#                                                      #
# Version    : 1.0                                     #
#                                                      #
########################################################

# Imports
from flask import Flask, redirect, request, jsonify, render_template, url_for, session
from flask_sqlalchemy import SQLAlchemy
from hashids import Hashids
import os

# Config
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  
app = Flask(__name__)
db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
SALT = 'Hashids SALT GOES HERE'

# Models
class Url(db.Model):
    # Create table `urls` |id|url|
    __tablename__ = "urls"
    id = db.Column(db.Integer, primary_key=True) 
    url = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, url):
        self.url = url


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True) 
    username = db.Column(db.String(50))
    password = db.Column(db.String(50))
    email = db.Column(db.String(150))
    urls = db.relationship("Url", backref="user")

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.email = email


# Controllers
@app.route('/sh', methods = ['GET', 'POST'])
def sh():
    # If it's a POST request:
    if request.method == 'POST':
        # Get link from HTML form
        link = request.args.get('link')
        # Basic link checker
        if link != "" and not link.count(' ') >= 1 and not link.count('.') == 0:
            # Add link to the Database
            if link[:4].lower() != 'http':
                link = 'http://{}'.format(link)
            db.session.add(Url(url=link)) 
            db.session.commit()
            # Get last added id
            url_id = db.session.query(Url).order_by(Url.id.desc()).first().id
            # Encode id (example: 3 => HFdK)
            id_code = Hashids(salt=SALT, min_length=4).encode(url_id)
            # Generate short link ('/HFdK')
            short_link = '/' + id_code  
            # Make a dictionary {'url_id': 3, 'short_link': '/HFdK'}
            urls = dict(url_id=url_id, short_link=short_link)
            # Convert urls dictionary to JSON and return it
            return jsonify(**urls) 
        else:
            return jsonify(**{'url_id':0, 'short_link':''})

    return render_template('index.html',
                           page='sh',
                           short_link = 'qssrtk.herokuapp.com/kRa0')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<id>')
def url(id):
    # Decode id (HFdK => 3)}}
    original_id = Hashids(salt=SALT, min_length=4).decode(id)
    if original_id:
        original_id = original_id[0]
        # Get original url ('get url where id = original_id')
        original_url = Url.query.filter_by(id=original_id).first().url
        return redirect(original_url , code=302)
    else:
        return render_template('index.html')

@app.route('/register', methods = ['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    user = User(username, password, email)
    db.session.add(user)
    db.session.commit()

@app.route('/login', methods = ['POST'])
def login():
    form_username = request.form['username']
    form_password = request.form['password']
    user = User.query.filter_by(username=form_username).first()
    if user:
        if user.username == form_username and user.password == form_password:
            session['logged_in'] = True
            flash('Logged in as {}'.format(user.username))
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
        urls = Url.query.all()
        return render_template('dashboard.html', urls = urls)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out!')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

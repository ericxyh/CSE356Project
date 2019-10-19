from flask import Flask, request, render_template, jsonify, make_response
from flask_mail import Mail, Message
from bson.objectid import ObjectId
import datetime, random, smtplib
from pymongo import MongoClient


client = MongoClient()
db = client.twitter
twiu = db.users

app = Flask(__name__)
mail = Mail(app)

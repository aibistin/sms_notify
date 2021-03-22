# app/__init__.py - API blueprint constructor
from flask import Blueprint


bp = Blueprint('api', __name__)


# Import after the Blueprint is created
from app.api import users, errors, tokens
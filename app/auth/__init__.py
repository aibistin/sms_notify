# app/auth/__init__.py
from flask import Blueprint

bp = Blueprint('auth', __name__)

# Import is at the bottom to avoid circular dependencies
from app.auth import routes

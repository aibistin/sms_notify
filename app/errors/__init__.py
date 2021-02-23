# app/errors/__init__.py
from flask import Blueprint

bp = Blueprint('errors', __name__)

# Import is at the bottom to avoid circular dependencies
from app.errors import handlers

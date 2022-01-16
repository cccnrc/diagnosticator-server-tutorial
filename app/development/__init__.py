from flask import Blueprint

bp = Blueprint( 'development', __name__ )

from app.development import routes

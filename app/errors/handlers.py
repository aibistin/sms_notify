from flask import render_template
from app import db
from app.errors import bp


# @app.errorhandler(404)
# Changed the above decorator to below to make the blueprint separate
#  from the application, and thus, more portable.
@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


# @app.errorhandler(500)
@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

from flask import Blueprint, render_template, current_app
import logging
from common.utils import load_cv_data  # Import the specific function

logger = logging.getLogger(__name__)

shell_bp = Blueprint('shell', __name__,
                     template_folder='templates',
                     static_folder='static',
                     static_url_path='/shell-static')


@shell_bp.route('/')
def selector():
    """Serves the initial view selector page."""
    logger.info("Serving view selector page.")
    cv_data = load_cv_data()  # Load CV data to get the name
    return render_template('selector.html', cv=cv_data)

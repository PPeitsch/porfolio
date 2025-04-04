from flask import Blueprint

cli_bp = Blueprint(
    'cli',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/cli-static'
)

# Import routes after blueprint definition to avoid circular imports
from . import routes

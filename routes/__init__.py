from routes.eod_summary import eod_summary
from routes.history import history

def register_routes(app):
    app.register_blueprint(eod_summary)
    app.register_blueprint(history)
    # Add more blueprints as needed

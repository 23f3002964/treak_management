from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    import os
    # Templates and static directories are set relative to this folder
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Ensure instance path exists (useful for SQLite or local logs)
    os.makedirs(app.instance_path, exist_ok=True)

    # Load configuration
    from application.config import Config
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints/routes
    from application.controllers import main_bp
    app.register_blueprint(main_bp)

    # Register error handlers
    from flask import render_template
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # Context processor for templates
    import datetime
    @app.context_processor
    def inject_now():
        return {'now': datetime.datetime.utcnow()}

    return app

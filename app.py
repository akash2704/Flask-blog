from flask import Flask
from extensions import db, bcrypt
from auth.routes import auth_bp
from blog.routes import blog_bp
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("APP_SECRET_KEY")

    # DB Config
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Init extensions
    db.init_app(app)
    bcrypt.init_app(app)

    # Blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(blog_bp)

    with app.app_context():
        db.create_all()

    return app

# <-- Add this top-level app for Gunicorn
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

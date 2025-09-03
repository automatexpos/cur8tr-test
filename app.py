import os
import logging
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_migrate import Migrate
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Create database instance
db = SQLAlchemy(model_class=Base)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration - Production-safe session handling
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")

    SUPABASE_PASSWORD = os.environ.get("SUPABASE_PASSWORD")
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")  # "development" or "production"

    if ENVIRONMENT == "production":
        # ✅ Use transaction pooler on Vercel
        app.config["SQLALCHEMY_DATABASE_URI"] = (f"postgresql://postgres.uhgwgylljeemqbmuhgqn:{SUPABASE_PASSWORD}@aws-1-us-west-1.pooler.supabase.com:6543/postgres"
)

        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": NullPool}
    else:
        # ✅ Local dev uses direct connection on 5432
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"postgresql+psycopg2://postgres:{SUPABASE_PASSWORD}"
            "@db.uhgwgylljeemqbmuhgqn.supabase.co:5432/postgres?sslmode=require"
        )
        # Local dev can use normal pooling
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True
        }

    # File upload configuration
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    
    # Cookie/session config
    is_production = (ENVIRONMENT == "production")
    app.config.update(
        SESSION_COOKIE_NAME="session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=is_production,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_REFRESH_EACH_REQUEST=True,
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        PREFERRED_URL_SCHEME="https" if is_production else "http",
    )
    
    # Proxy middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    with app.app_context():
        from models import User, Profile, Category, Recommendation
        
        # ✅ Only create tables locally, never on Vercel
        if ENVIRONMENT != "production":
            db.create_all()

        # Seed admin user if SEED=1
        if os.environ.get("SEED") == "1":
            from werkzeug.security import generate_password_hash
            admin = User.query.filter_by(username="admin").first()
            if not admin:
                admin = User(
                    username="admin",
                    email="admin@cur8tr.com",
                    password_hash=generate_password_hash("admin123"),
                    is_admin=True,
                    is_verified=True
                )
                db.session.add(admin)
                db.session.commit()
                logging.info("Admin user created: admin/admin123")
    
    # Register routes
    from routes import register_routes
    register_routes(app, db)
    
    from routes_probe import probe
    app.register_blueprint(probe)
    
    return app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

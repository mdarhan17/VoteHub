from flask import Flask
from config import Config
from app.extensions import mysql

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mysql.init_app(app)

    from app.routes.auth_routes import auth_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.voter_routes import voter_bp
    from app.routes.candidate_routes import candidate_bp
    from app.routes.election_routes import election_bp
    from app.routes.vote_routes import vote_bp
    from app.routes.result_routes import result_bp
    from app.routes.public_result_routes import public_result_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(voter_bp)
    app.register_blueprint(candidate_bp)
    app.register_blueprint(election_bp)
    app.register_blueprint(vote_bp)
    app.register_blueprint(result_bp)
    app.register_blueprint(public_result_bp)

    return app

from flask import Flask, Blueprint

test_bp = Blueprint('test', __name__)

@test_bp.route('/')
def index():
    return "Test Index Route funktioniert!"

def create_test_app():
    app = Flask(__name__)
    app.register_blueprint(test_bp)
    return app

if __name__ == "__main__":
    app = create_test_app()
    app.run(debug=True)

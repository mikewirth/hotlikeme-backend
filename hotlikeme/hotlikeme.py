from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_potion import Api, ModelResource

app = Flask(__name__)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    age = db.Column(db.Integer)

db.create_all()

class UserResource(ModelResource):
    class Meta:
        model = User
        name = "users"

api = Api(app)
api.add_resource(UserResource)

if __name__ == '__main__':
    app.run()

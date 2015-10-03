from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from flask_potion import Api, ModelResource

app = Flask(__name__)
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'Users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    age = db.Column(db.Integer)

class Comparison(db.Model):
    __tablename__ = 'Comparisons'

    id = db.Column(db.Integer, primary_key=True)
    evaluator_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)

    male = db.relationship(User)
    female = db.relationship(User)
    outcome = db.Column(db.Enum("open", "equal", "male", "female"))

    evaluator = db.relationship(User, backref=backref('comparisons', lazy='dynamic'))

db.create_all()

class UserResource(ModelResource):
    class Meta:
        model = User
        name = "users"

api = Api(app)
api.add_resource(UserResource)

if __name__ == '__main__':
    app.run()

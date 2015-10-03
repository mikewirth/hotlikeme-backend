from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from marshmallow import Schema, fields


app = Flask(__name__)
app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///../test.db")

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'Users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    profilePic = db.Column(db.String, nullable=False)
    gender = db.Column(db.Enum("male", "female"), nullable=False)
    age = db.Column(db.Integer)

    matchRank = None
    exactMatches = None

    def calculateMatches(self):
        # TODO(fubu): calculate real values
        self.matchRank = 10
        self.exactMatches = 5


class Comparison(db.Model):
    __tablename__ = 'Comparisons'

    id = db.Column(db.Integer, primary_key=True)

    evaluator_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    evaluator = db.relationship(
        User, primaryjoin=evaluator_id == User.id,
        backref=backref('comparisons', lazy='dynamic')
    )

    male_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    male = db.relationship(User, primaryjoin=male_id == User.id)

    female_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    female = db.relationship(User, primaryjoin=female_id == User.id)

    outcome = db.Column(
        db.Enum("open", "equal", "male", "female"),
        default="open", server_default="open"
    )


class UserSchema(Schema):
    class Meta:
        model = User
        fields = ('id', 'name', 'profilePic', 'age', 'gender')
        sqla_session = db.session

user_schema = UserSchema()

@app.route('/api/users/<id>')
def user_detail(id):
    user = User.query.get(id)
    res = user_schema.dump(user).data
    return jsonify(res)

@app.route('/api/users', methods=['GET', 'POST', 'PUT'])
def users():
    if request.method == 'GET':
        res = user_schema.dump(User.query.all(), many=True).data
        return jsonify(results=res)
    elif request.method == 'POST':
        user = User(**user_schema.load(request.json).data)
        db.session.add(user)
        db.session.commit()
        return jsonify( user_schema.dump(user).data )
    elif request.method == 'PUT':
        parameters = user_schema.load(request.json).data
        user = User.query.get(parameters['id'])
        for k,v in parameters.iteritems():
            setattr(user, k, v)
        db.session.commit()
        return jsonify( user_schema.dump(user).data )


class ComparisonSchema(Schema):

    evaluator = fields.Nested(UserSchema)
    male = fields.Nested(UserSchema)
    female = fields.Nested(UserSchema)

    class Meta:
        model = Comparison
        fields = ("id", "evaluator", "male", "female", "outcome")
        sqla_session = db.session

comparison_schema = ComparisonSchema()


@app.route('/api/comparisons')
def comparisons():
    if request.method == 'GET':
        res = comparison_schema.dump(Comparison.query.all(), many=True).data
        return jsonify(results=res)


if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    db.session.add_all([
        User(name="Tim Tester", profilePic="facbook.com/1", gender="male", age=25),
        User(name="Tina Testerin", profilePic="facbook.com/2", gender="female"),
        User(name="Max Mustermann", profilePic="facbook.com/3", gender="male", age=45),
        Comparison(evaluator_id=1, male_id=3, female_id=2),
    ])
    db.session.commit()

    app.run(debug=True)

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import orm, Index, func
from marshmallow import Schema, fields
import random


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
        backref=orm.backref('comparisons', lazy='dynamic')
    )

    male_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    male = db.relationship(User, primaryjoin=male_id == User.id)

    female_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    female = db.relationship(User, primaryjoin=female_id == User.id)

    outcome = db.Column(
        db.Enum("open", "equal", "male", "female"),
        default="open", server_default="open"
    )

    __table_args__ = (
        Index(evaluator_id, male_id, female_id, unique=True),
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
def comparisons(comparison_id=None):
    evaluator_id = request.args.get('evaluator')

    qry = Comparison.query.filter(Comparison.outcome == "open")
    if evaluator_id is not None:
        NUM_NEW_COMPS = 10
        evaluator = User.query.get(evaluator_id)
        qry = qry.filter(Comparison.evaluator_id == int(evaluator_id))

        # If not yet NUM_NEW_COMPS open comparisons, generate some
        if qry.count() < NUM_NEW_COMPS:
            returned_comparisons = set()        # contains (<user male>, <user female>) tuples

            for c in qry:
                returned_comparisons.add( (c.male, c.female) )

            users_without_evaluator = User.query.filter(User.id != evaluator.id)
            males = users_without_evaluator.filter(User.gender == "male")
            females = users_without_evaluator.filter(User.gender == "female")

            print males.count()
            print females.count()
            
            while len(returned_comparisons) < min(males.count() * females.count(), NUM_NEW_COMPS):

                random_tuple = (random.sample(set(males),1)[0], random.sample(set(females),1)[0])
                if not random_tuple in returned_comparisons:
                    comp = Comparison()
                    comp.evaluator = evaluator
                    comp.male = random_tuple[0]
                    comp.female = random_tuple[1] 
                    db.session.add(comp)
                    db.session.commit()
                    returned_comparisons.add(random_tuple)

    res = comparison_schema.dump(qry.all(), many=True).data
    return jsonify(results=res)


@app.route('/api/comparisons/<int:comparison_id>', methods=['PUT'])
def update_comparison(comparison_id):
    comparison = Comparison.query.get(comparison_id)

    data = comparison_schema.load(request.json).data
    for k, v in data.iteritems():
        setattr(comparison, k, v)
    db.session.commit()

    return jsonify(comparison_schema.dump(comparison).data)


if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    db.session.add_all([
        User(id=1, name="Tim Tester", profilePic="facbook.com/1", gender="male", age=25),
        User(id=2, name="Bruce Wayne", profilePic="facbook.com/2", gender="male", age=40),
        user(id=3, name="tina testerin", profilepic="facbook.com/2", gender="female"),
        user(id=4, name="martina martinsson", profilepic="facbook.com/4", gender="female"),
        User(id=5, name="Max Mustermann", profilePic="facbook.com/5", gender="male", age=45),
        Comparison(evaluator_id=1, male_id=2, female_id=3),
        Comparison(evaluator_id=2, male_id=1, female_id=3)
    ])
    db.session.commit()

    app.run(host="0.0.0.0", debug=True)

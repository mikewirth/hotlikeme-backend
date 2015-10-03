from flask import Flask, jsonify, request, session, abort
from flask.ext.cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc, orm, Index
from marshmallow import Schema, fields
from trueskill import Rating, rate_1vs1


app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI="sqlite:///../test.db",
    SECRET_KEY="really-really-secret-key!",
    SESSION_COOKIE_HTTPONLY=False,
    CORS_SUPPORTS_CREDENTIALS=True,
)

CORS(app, resources=r'/api/')

db = SQLAlchemy(app)


@app.before_request
def set_current_user():
    if "userid" in session:
        user = User.query.get(int(session['userid']))
        if user is None:
            session.pop('userid')


class User(db.Model):
    __tablename__ = 'Users'

    # The user id is the facebook id of the user
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)

    name = db.Column(db.String(), nullable=False)
    profilePic = db.Column(db.String, nullable=False)
    gender = db.Column(db.Enum("male", "female"), nullable=False)
    age = db.Column(db.Integer)

    score = db.Column(db.Float, default=25.0, server_default="25.0")
    sigma = db.Column(db.Float, default=8.333, server_default="8.333")

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
        Index("udx_single_comparisons", evaluator_id, male_id, female_id,
              unique=True),
    )


class UserSchema(Schema):
    class Meta:
        model = User
        fields = ('id', 'name', 'profilePic', 'age', 'gender', 'score', 'sigma')
        sqla_session = db.session

user_schema = UserSchema()


@app.route("/api/users/me")
def get_current_user():
    user = None
    if "userid" in session:
        user = User.query.get(session['userid'])

    return jsonify(user_schema.dump(user).data)


@app.route('/api/users/<id>')
def user_detail(id):
    user = User.query.get(id)
    if user is None:
        abort(404)

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
        try:
            db.session.commit()
        except exc.IntegrityError:
            db.session.rollback()
            user = User.query.get(request.json['id'])

        session['userid'] = user.id
        return jsonify(user_schema.dump(user).data)

    elif request.method == 'PUT':
        parameters = user_schema.load(request.json).data
        user = User.query.get(parameters['id'])
        for k, v in parameters.iteritems():
            setattr(user, k, v)
        db.session.commit()
        return jsonify(user_schema.dump(user).data)


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
    NUM_NEW_COMPS = 10

    evaluator_id = session.get('userid')
    evaluator_comparisons_qry = Comparison.query.filter_by(evaluator_id=evaluator_id)

    comparisons = []
    if evaluator_id is not None:
        open_comparisons = evaluator_comparisons_qry.filter_by(outcome="open").all()
        if len(open_comparisons) < NUM_NEW_COMPS:
            # Get all existing comparisons
            existing_comparisons = set(
                (c.male_id, c.female_id) for c in evaluator_comparisons_qry
            )

            # Get all users the evaluator has not yet compared
            all_males = set()
            all_females = set()
            all_users = db.session.query(User.id, User.gender).filter(
                User.id != evaluator_id
            ).all()
            for userid, gender in all_users:
                target = all_males if gender == "male" else all_females
                target.add(userid)

            max_tries = (
                (len(all_males) - 1) * (len(all_females) - 1)
                - len(existing_comparisons)
            )
            tries = 0
            while (len(open_comparisons) < NUM_NEW_COMPS and tries < max_tries):
                tries += 1

                male, female = all_males.pop(), all_females.pop()
                if (male, female) in existing_comparisons:
                    all_males.add(male)
                    all_females.add(female)
                    continue

                new_open_comparison = Comparison(
                    evaluator_id=evaluator_id, male_id=male, female_id=female
                )
                db.session.add(new_open_comparison)
                db.session.flush()
                open_comparisons.append(new_open_comparison)

        db.session.commit()
        comparisons = comparison_schema.dump(open_comparisons, many=True).data

    return jsonify(results=comparisons)


@app.route('/api/comparisons/<int:comparison_id>', methods=['PUT'])
def update_comparison(comparison_id):
    comparison = Comparison.query.get(comparison_id)
    if comparison is None:
        abort(404)

    outcome = request.json.get('outcome')
    if outcome in (None, "open"):
        abort(400)

    comparison.outcome = outcome
    
    winner = getattr(comparison, comparison.outcome)
    loser = getattr(comparison, "male" if outcome == "female" else "female")
    winner_rat = Rating(mu=winner.score, sigma=winner.sigma)
    loser_rat = Rating(mu=loser.score, sigma=loser.sigma)
    new_winner_rat, new_loser_rat = rate_1vs1(winner_rat, loser_rat, drawn=True if outcome == "equal" else False)
    print(winner)
    print(loser)
    setattr(winner, "score", new_winner_rat.mu)
    setattr(winner, "sigma", new_winner_rat.sigma)
    setattr(loser, "score", new_loser_rat.mu)
    setattr(loser, "sigma", new_loser_rat.sigma)


    db.session.commit()
    return jsonify(comparison_schema.dump(comparison).data)

@app.route('/api/couples')
def top_couples():
    res = db.engine.connect().execute("select * from Users")
    for r in res:
        print("lololol")
    return "lol"


if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    #db.session.add_all([
    #    User(id=1, name="Tim Tester", profilePic="facbook.com/1", gender="male", age=25),
    #    User(id=2, name="Bruce Wayne", profilePic="facbook.com/2", gender="male", age=40),
    #    User(id=3, name="tina testerin", profilePic="facbook.com/2", gender="female"),
    #    User(id=4, name="martina martinsson", profilePic="facbook.com/4", gender="female"),
    #    User(id=5, name="Max Mustermann", profilePic="facbook.com/5", gender="male", age=45),
    #    Comparison(evaluator_id=1, male_id=2, female_id=3),
    #    Comparison(evaluator_id=2, male_id=1, female_id=3)
    #])
    db.session.commit()

    app.run(host="0.0.0.0", debug=True)

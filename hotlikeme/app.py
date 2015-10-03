from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from flask_potion import Api, ModelResource, fields, routes, resource


app = Flask(__name__)
app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///../test.db")

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'Users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    profilePic = db.Column(db.String, nullable=False)
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


db.create_all()


class UserResource(ModelResource):

    class Meta:
        model = User
        name = "users"
        read_only_fields = ["matchRank", "exactMatches"]

    class Schema:
        matchRank = fields.Integer()
        exactMatches = fields.Integer()

    @routes.ItemRoute.GET("/matches", response_schema=resource.Inline('self'))
    def user_matches(self, user):
        user.calculateMatches()
        return user


class ComparisonResource(ModelResource):

    class Meta:
        model = Comparison
        name = "comparisons"

    class Schema:
        evaluator = fields.Inline("users")
        male = fields.Inline("users")
        female = fields.Inline("users")


api = Api(app)
api.add_resource(UserResource)
api.add_resource(ComparisonResource)

if __name__ == '__main__':
    app.run(debug=True)

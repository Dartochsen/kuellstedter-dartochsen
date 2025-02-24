from app.extensions import db

class ForumThema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titel = db.Column(db.String(150), nullable=False)
    inhalt = db.Column(db.Text, nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    datum = db.Column(db.DateTime, default=db.func.current_timestamp())
    antworten = db.relationship('Antwort', backref='thema', lazy=True)

    def __repr__(self):
        return f'<ForumThema "{self.titel}">'

class Antwort(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inhalt = db.Column(db.Text, nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    thema_id = db.Column(db.Integer, db.ForeignKey('forum_thema.id'), nullable=False)

    def __repr__(self):
        return f'<Antwort "{self.inhalt[:20]}...">'

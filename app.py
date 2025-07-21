from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///donghua.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Database model
class Donghua(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    last_episode = db.Column(db.Integer, nullable=False)


# ✅ Main home page route
@app.route("/")
def index():
    donghuas = Donghua.query.order_by(Donghua.title.asc()).all()
    return render_template("index.html", donghuas=donghuas)


# Add new donghua
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        title = request.form["title"]
        episode = request.form["episode"]
        print("Adding:", title, episode)

        new_donghua = Donghua(title=title, last_episode=int(episode))
        db.session.add(new_donghua)
        db.session.commit()
        return redirect("/")
    return render_template("add.html")


# Delete a donghua
@app.route("/delete/<int:id>")
def delete(id):
    donghua = Donghua.query.get_or_404(id)
    db.session.delete(donghua)
    db.session.commit()
    return redirect("/")


# Update donghua
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    donghua = Donghua.query.get_or_404(id)
    donghua.title = request.form["title"]
    donghua.last_episode = int(request.form["episode"])
    db.session.commit()
    return redirect("/")


# Initialize database
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

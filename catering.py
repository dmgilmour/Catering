from flask import Flask, request, abort, url_for, redirect, session, render_template, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catering.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


staff_list = db.Table('staff_list',
        db.Column('staff_id', db.Integer, db.ForeignKey('staff.id')),
        db.Column('event_id', db.Integer, db.ForeignKey('event.id'))
)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    name = db.Column(db.String(50))
    date = db.Column(db.String(50))
    staff_list = db.relationship('Staff', secondary=staff_list, backref=db.backref('event_list', lazy='dynamic'))

    def __init__(self, name, date):
        self.name = name
        self.date = date


class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(50))

    def __init__(self, name, password):
        self.name = name
        self.password = password


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(50))
    event_list = db.relationship('Event', backref='customer', lazy='dynamic')

    def __init__(self, name, password):
        self.name = name
        self.password = password



@app.cli.command("initdb")
def initdb_command():

    db.drop_all()
    db.create_all()

    db.session.commit()

@app.cli.command("check")
def default():

    customers = Customer.query.all()
    for c in customers:
        print("")
        print(c.name)
        for e in c.event_list:
            print("    ", e.name)
            for s in e.staff_list:
                print("        ", s.name)


@app.route("/")
def default():
    if "user" in session:
        if not Customer.query.filter_by(name=session["user"]).first() and not Staff.query.filter_by(name=session["user"]).first():
            session.clear()
            return redirect(url_for("login"))
        else:
            return redirect(url_for(session["usertype"]))

    else:
        return redirect(url_for("login"))


@app.route("/login/", methods = ["GET", "POST"])
def login():
    message = ""

    if "user" in session:
        return redirect(url_for(session["usertype"]))

    elif request.method == "POST":

        if request.form["user"] == "owner":
            if request.form["pass"] == "pass":
                session["user"] = "owner"
                session["usertype"] = "owner"
                return redirect(url_for("owner"))
        else:
            user = Customer.query.filter_by(name = request.form["user"]).first()
            if user:
                if user.password == request.form["pass"]:
                    session["user"] = user.name
                    session["usertype"] = "customer"
                    return redirect(url_for("customer"))
            user = Staff.query.filter_by(name = request.form["user"]).first()
            if user:
                if user.password == request.form["pass"]:
                    session["user"] = user.name
                    session["usertype"] = "staff"
                    return redirect(url_for("staff"))

            message = "Invalid credentials"

    return render_template("login.html", message=message)


@app.route("/signup/", methods = ["GET", "POST"])
def signup():

    message = ""

    if request.method == "POST":
        username = request.form["user"]
        if Customer.query.filter_by(name = username).first() or Staff.query.filter_by(name = username).first() or username == "owner":
            message = "Username already taken"
        else:
            db.session.add(Customer(request.form["user"], request.form["pass"]))
            db.session.commit()
            message = "New user account created"
    return render_template("signup.html", message=message)
        




@app.route("/customer/", methods = ["GET", "POST"])
def customer():
    if "usertype" not in session or session["usertype"] != "customer":
        return redirect(url_for("default"))
    user = Customer.query.filter_by(name=session["user"]).first()
    if request.method == "POST":
        Event.query.filter_by(name=next(iter(request.form.values()))).delete()
        db.session.commit()
    return render_template("customer.html", events=user.event_list)


@app.route("/staff/", methods = ["GET", "POST"])
def staff():
    if "usertype" not in session or session["usertype"] != "staff":
        return redirect(url_for("default"))
    user = Staff.query.filter_by(name=session["user"]).first()
    if request.method == "POST":
        event = Event.query.filter_by(name=next(iter(request.form.values()))).first()
        event.staff_list.append(user)
        db.session.commit()
    
    event_list = Event.query.all()
    staff_events = user.event_list
    event_list = [event for event in event_list if event not in staff_events and len(event.staff_list) < 3]
    return render_template("staff.html", events_attending=staff_events, events_attendable=event_list)


@app.route("/owner/")
def owner():
    if "usertype" not in session or session["usertype"] != "owner":
        return redirect(url_for("default"))
    event_list = Event.query.all()

    return render_template("owner.html", event_list=event_list)

@app.route("/owner/register/", methods = ["GET", "POST"])
def register():
    if "usertype" not in session or session["usertype"] != "owner":
        return redirect(url_for("default"))

    message = "" 

    if request.method == "POST":
        username = request.form["user"]
        if Customer.query.filter_by(name = username).first() or Staff.query.filter_by(name = username).first() or username == "owner":
            message = "Username already taken"
        else:
            db.session.add(Staff(request.form["user"], request.form["pass"]))
            db.session.commit()
            message = "Sucessfully created new user"
    return render_template("register.html", message=message)

    
@app.route("/customer/event/", methods = ["GET", "POST"])
def event():
    if "usertype" not in session or session["usertype"] != "customer":
        return redirect(url_for("default"))

    message = "" 

    if request.method == "POST":
        name = request.form["name"]
        date = request.form["date"]
        if Event.query.filter_by(date=date).first():
            message = "Date unavailable"
        else:
            customer = Customer.query.filter_by(name=session["user"]).first()
            customer.event_list.append(Event(request.form["name"], request.form["date"]))
            db.session.commit()
            message = "Sucessfully created new event"
    return render_template("event.html", message=message)

@app.route("/logout/")
def logout():
    if "user" in session:
        session.clear()
    return redirect(url_for("login"))


app.secret_key = "git git git brrrrrwrwrwaaaahh"

if __name__ == "__main__":
    app.run()

import enum

from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, select, ForeignKey, Enum, func
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from dotenv import load_dotenv
import os
from forms import SignUpForm, VerificationForm, LoginForm
from random import randint
from send_verification import Smtp_verification

load_dotenv()
verification_sender_mail = os.getenv('MAIL_USERNAME')
mail_host = os.getenv('MAIL_SERVER')
mail_port = os.getenv('MAIL_PORT')
mail_password = os.getenv('MAIL_PASSWORD')

app = Flask(__name__)
app.config['SECRET_KEY']= os.environ['SECRET_KEY']

db = SQLAlchemy()


class Base(DeclarativeBase):
    pass


class MissionStatus(enum.Enum):
    in_progress = "in progress"
    finished = "finished"


class ToDo(Base):
    __tablename__ = 'todo'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    task_name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[MissionStatus] = mapped_column(
        Enum(MissionStatus, name="mission_status", default=MissionStatus.in_progress)
    )
    user: Mapped["User"] = relationship(back_populates="tasks")

class User(Base, UserMixin):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(200), nullable=False)
    tasks: Mapped[list["ToDo"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # or PostgreSQL/MySQL URI
db.init_app(app)

with app.app_context():
    engine = db.engine
    Base.metadata.create_all(engine)
    db.create_all()

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)



@app.route("/")
def home():
    return render_template('home.html')


@app.route("/sign-up", methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = SignUpForm()
    if form.validate_on_submit():
        existing_user = db.session.query(User).filter_by(email=form.email.data).first()
        if existing_user:
            flash("An account with that email already exists. Please log in instead.", "warning")
            return redirect(url_for('signup'))

        session['signup_email'] = form.email.data
        session['signup_name'] = form.name.data
        session['signup_password'] = form.password.data
        session['verification_code'] = str(randint(100000, 999999))
        verifying_mail = Smtp_verification(mail_username=verification_sender_mail,
                          mail_host=mail_host,
                          mail_password=mail_password,
                          mail_port=mail_port)
        msg = f"Hey {form.name.data}, {session['verification_code']} is your code to verify your account."
        verifying_mail.send_code(message=msg, to_address=form.email.data)
        return redirect(url_for('verify'))
    return render_template('signup.html', form=form)


@app.route("/verify", methods=['GET', 'POST'])
def verify():
    if 'verification_code' not in session or 'signup_email' not in session:
        return redirect(url_for('home'))

    code_to_send = session['verification_code']
    account_form = VerificationForm(expected_code=code_to_send)
    print(code_to_send)
    # If validation code correct login and redirect to home
    if account_form.validate_on_submit():
        new_user = User(
            name=session.get('signup_name'),
            email=session.get('signup_email'),
            password=generate_password_hash(session.get('signup_password')),
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)


        return redirect(url_for('home'))
    return render_template('verify.html', form=account_form)


@app.route("/login", methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('home'))
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = db.session.scalar(select(User).where(User.email == login_form.email.data))
        if check_password_hash(user.password, login_form.password.data) and user:
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Email or password incorrect, try again!', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html', form=login_form)


@app.route("/faqs")
def faqs():
    return render_template('faqs.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('home'))


@app.route("/conquer", methods=['GET', 'POST'])
@login_required
def conquer():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "save":
            title = (request.form.get("title") or "").strip()
            if title:
                new_task = ToDo(
                    task_name=title,
                    user_id=current_user.id,
                    status=MissionStatus.in_progress
                )
                db.session.add(new_task)
                db.session.commit()
        elif action:
            task_id = request.form.get("task_id")
            task = db.session.query(ToDo).filter_by(id=task_id, user_id=current_user.id).first()
            if task:
                if action == "delete":
                    db.session.delete(task)
                    db.session.commit()
                elif action == "finish":
                    task.status = MissionStatus.finished
                    db.session.commit()
        return redirect(url_for("conquer"))
    tasks = db.session.query(ToDo).filter_by(user_id=current_user.id).order_by(ToDo.id.asc()).all()

    return render_template("conquer.html", tasks=tasks)


@app.route("/pricing")
def pricing():
    return render_template("pricing.html")

if __name__ == '__main__':
    app.run(debug=True)
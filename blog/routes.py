from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from models import Post, Comment

blog_bp = Blueprint("blog", __name__, template_folder="../templates")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

@blog_bp.route("/")
def home():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template("home.html", posts=posts)

@blog_bp.route("/post/<int:post_id>", methods=["GET", "POST"])
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == "POST":
        if "user_id" not in session:
            flash("You must be logged in to comment.", "danger")
            return redirect(url_for("auth.login"))
        content = request.form["content"]
        new_comment = Comment(content=content, user_id=session["user_id"], post_id=post.id)
        db.session.add(new_comment)
        db.session.commit()
        flash("Comment added!", "success")
        return redirect(url_for("blog.post_detail", post_id=post.id))

    return render_template("post_detail.html", post=post)

@blog_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        new_post = Post(title=title, content=content, user_id=session["user_id"])
        db.session.add(new_post)
        db.session.commit()
        flash("Post created successfully!", "success")
        return redirect(url_for("blog.home"))

    return render_template("create_post.html")

@blog_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html", name=session["user_name"])
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from models import Post, Comment

blog_bp = Blueprint("blog", __name__, template_folder="../templates")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

@blog_bp.route("/")
def home():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template("home.html", posts=posts)

@blog_bp.route("/post/<int:post_id>", methods=["GET", "POST"])
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == "POST":
        if "user_id" not in session:
            flash("You must be logged in to comment.", "danger")
            return redirect(url_for("auth.login"))
        content = request.form["content"]
        new_comment = Comment(content=content, user_id=session["user_id"], post_id=post.id)
        db.session.add(new_comment)
        db.session.commit()
        flash("Comment added!", "success")
        return redirect(url_for("blog.post_detail", post_id=post.id))

    return render_template("post_detail.html", post=post)

@blog_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        new_post = Post(title=title, content=content, user_id=session["user_id"])
        db.session.add(new_post)
        db.session.commit()
        flash("Post created successfully!", "success")
        return redirect(url_for("blog.home"))

    return render_template("create_post.html")

@blog_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html", name=session["user_name"])

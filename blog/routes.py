from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from extensions import db
from models import Post, Comment, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps

blog_bp = Blueprint("blog", __name__, template_folder="../templates")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

# Web Routes
@blog_bp.route("/")
def home():
    posts = Post.query.filter_by(is_public=True).order_by(Post.timestamp.desc()).all()
    return render_template("home.html", posts=posts)

@blog_bp.route("/post/<int:post_id>", methods=["GET", "POST"])
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Check if post is public or user owns it
    if not post.is_public and session.get("user_id") != post.user_id:
        flash("This post is private.", "warning")
        return redirect(url_for("blog.home"))
    
    if request.method == "POST":
        if "user_id" not in session:
            flash("You must be logged in to comment.", "danger")
            return redirect(url_for("auth.login"))
        
        content = request.form["content"].strip()
        if content:
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
        title = request.form["title"].strip()
        content = request.form["content"].strip()
        is_public = request.form.get("is_public", "on") == "on"

        if title and content:
            new_post = Post(
                title=title, 
                content=content, 
                user_id=session["user_id"],
                is_public=is_public
            )
            db.session.add(new_post)
            db.session.commit()
            flash("Post created successfully!", "success")
            return redirect(url_for("blog.home"))
        else:
            flash("Title and content are required.", "danger")

    return render_template("create_post.html")

@blog_bp.route("/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Check if user owns the post
    if post.user_id != session["user_id"]:
        flash("You can only edit your own posts.", "danger")
        return redirect(url_for("blog.home"))
    
    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()
        is_public = request.form.get("is_public", "off") == "on"
        
        if title and content:
            post.title = title
            post.content = content
            post.is_public = is_public
            db.session.commit()
            flash("Post updated successfully!", "success")
            return redirect(url_for("blog.post_detail", post_id=post.id))
        else:
            flash("Title and content are required.", "danger")
    
    return render_template("edit_post.html", post=post)

@blog_bp.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Check if user owns the post
    if post.user_id != session["user_id"]:
        flash("You can only delete your own posts.", "danger")
        return redirect(url_for("blog.home"))
    
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully!", "success")
    return redirect(url_for("blog.profile"))

@blog_bp.route("/profile")
@login_required
def profile():
    user = User.query.get(session["user_id"])
    user_posts = Post.query.filter_by(user_id=session["user_id"]).order_by(Post.timestamp.desc()).all()
    return render_template("profile.html", user=user, posts=user_posts)

@blog_bp.route("/my-posts")
@login_required
def my_posts():
    posts = Post.query.filter_by(user_id=session["user_id"]).order_by(Post.timestamp.desc()).all()
    return render_template("my_posts.html", posts=posts)

# API Routes
@blog_bp.route("/api/posts", methods=["GET"])
def api_get_posts():
    posts = Post.query.filter_by(is_public=True).order_by(Post.timestamp.desc()).all()
    return jsonify({'posts': [post.to_dict() for post in posts]}), 200

@blog_bp.route("/api/posts", methods=["POST"])
@jwt_required()
def api_create_post():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'error': 'Title and content are required'}), 400
    
    post = Post(
        title=data['title'],
        content=data['content'],
        user_id=user_id,
        is_public=data.get('is_public', True)
    )
    db.session.add(post)
    db.session.commit()
    
    return jsonify({'post': post.to_dict()}), 201

@blog_bp.route("/api/posts/<int:post_id>", methods=["GET"])
def api_get_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if not post.is_public:
        return jsonify({'error': 'Post is private'}), 403
    
    return jsonify({'post': post.to_dict()}), 200

@blog_bp.route("/api/posts/<int:post_id>", methods=["PUT"])
@jwt_required()
def api_update_post(post_id):
    user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if data.get('title'):
        post.title = data['title']
    if data.get('content'):
        post.content = data['content']
    if 'is_public' in data:
        post.is_public = data['is_public']
    
    db.session.commit()
    return jsonify({'post': post.to_dict()}), 200

@blog_bp.route("/api/posts/<int:post_id>", methods=["DELETE"])
@jwt_required()
def api_delete_post(post_id):
    user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Post deleted successfully'}), 200

@blog_bp.route("/api/posts/<int:post_id>/comments", methods=["GET"])
def api_get_comments(post_id):
    post = Post.query.get_or_404(post_id)
    
    if not post.is_public:
        return jsonify({'error': 'Post is private'}), 403
    
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.timestamp.desc()).all()
    return jsonify({'comments': [comment.to_dict() for comment in comments]}), 200

@blog_bp.route("/api/posts/<int:post_id>/comments", methods=["POST"])
@jwt_required()
def api_create_comment(post_id):
    user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'error': 'Content is required'}), 400
    
    if not post.is_public:
        return jsonify({'error': 'Cannot comment on private posts'}), 403
    
    comment = Comment(
        content=data['content'],
        user_id=user_id,
        post_id=post_id
    )
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({'comment': comment.to_dict()}), 201

@blog_bp.route("/api/my-posts", methods=["GET"])
@jwt_required()
def api_get_my_posts():
    user_id = get_jwt_identity()
    posts = Post.query.filter_by(user_id=user_id).order_by(Post.timestamp.desc()).all()
    return jsonify({'posts': [post.to_dict() for post in posts]}), 200
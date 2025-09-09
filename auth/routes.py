from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
from extensions import db, bcrypt, mail, oauth
from models import User
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
import secrets
import requests

auth_bp = Blueprint("auth", __name__, template_folder="../templates")

# Configure Google OAuth
def init_oauth(app):
    oauth.init_app(app)
    google = oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    return google

# Serializer for generating/validating tokens
def generate_serializer():
    secret_key = current_app.config["SECRET_KEY"]
    return URLSafeTimedSerializer(secret_key)

# Email utilities
def send_confirmation_email(user, token):
    confirm_url = url_for("auth.confirm_email", token=token, _external=True)
    msg = Message(
        "Confirm Your Email - Flask Blog",
        recipients=[user.email],
    )
    msg.body = f"""Hello {user.name},

Please confirm your email by clicking this link:
{confirm_url}

This link will expire in 1 hour.

If you didn't create this account, please ignore this email.
"""
    mail.send(msg)

def send_reset_email(user, token):
    reset_url = url_for("auth.reset_password", token=token, _external=True)
    msg = Message(
        "Password Reset Request - Flask Blog",
        recipients=[user.email],
    )
    msg.body = f"""Hello {user.name},

A password reset has been requested for your account. Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request this reset, please ignore this email.
"""
    mail.send(msg)

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form.get("confirm_password", "")

        # Validation
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("signup.html")
        
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("signup.html")

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash("Email is already registered. Please log in.", "danger")
            return redirect(url_for("auth.login"))

        # Create user
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(name=name, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        # Generate confirmation token
        s = generate_serializer()
        token = s.dumps(email, salt="email-confirm")

        # Send confirmation email
        try:
            send_confirmation_email(new_user, token)
            flash("Signup successful! Please check your email to confirm your account.", "info")
        except Exception as e:
            flash("Account created but email confirmation failed. Please contact support.", "warning")
        
        return redirect(url_for("auth.login"))

    return render_template("signup.html")

@auth_bp.route("/confirm/<token>")
def confirm_email(token):
    s = generate_serializer()
    try:
        email = s.loads(token, salt="email-confirm", max_age=3600)  # 1 hour expiry
    except SignatureExpired:
        flash("The confirmation link has expired.", "danger")
        return redirect(url_for("auth.signup"))
    except BadSignature:
        flash("Invalid confirmation token.", "danger")
        return redirect(url_for("auth.signup"))

    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash("Account already confirmed. Please login.", "info")
    else:
        user.confirmed = True
        db.session.commit()
        flash("Your account has been confirmed! You can now login.", "success")

    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        remember_me = request.form.get("remember_me", False)

        user = User.query.filter_by(email=email).first()

        if user and user.password and bcrypt.check_password_hash(user.password, password):
            if not user.confirmed:
                flash("Please confirm your email before logging in.", "warning")
                return redirect(url_for("auth.login"))

            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Set session
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_email"] = user.email
            session.permanent = bool(remember_me)
            
            flash("Login successful!", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for("blog.home"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html")

# Google OAuth routes
@auth_bp.route("/google")
def google_login():
    google = init_oauth(current_app)
    redirect_uri = url_for("auth.google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@auth_bp.route("/google/callback")
def google_callback():
    google = init_oauth(current_app)
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if user_info:
        email = user_info['email']
        name = user_info['name']
        google_id = user_info['sub']
        avatar_url = user_info.get('picture')

        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Update existing user with Google info
            user.google_id = google_id
            user.avatar_url = avatar_url
            user.confirmed = True  # Google users are automatically confirmed
            user.last_login = datetime.utcnow()
        else:
            # Create new user
            user = User(
                name=name,
                email=email,
                google_id=google_id,
                avatar_url=avatar_url,
                confirmed=True
            )
            db.session.add(user)
        
        db.session.commit()
        
        # Set session
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email
        
        flash(f"Welcome {name}! Successfully logged in with Google.", "success")
        return redirect(url_for("blog.home"))
    
    flash("Google login failed. Please try again.", "danger")
    return redirect(url_for("auth.login"))

# Password Reset
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = user.generate_reset_token()
            try:
                send_reset_email(user, token)
                flash("Password reset instructions have been sent to your email.", "info")
            except Exception as e:
                flash("Failed to send reset email. Please try again later.", "danger")
        else:
            # Don't reveal if email exists or not
            flash("If that email is registered, you will receive reset instructions.", "info")
        
        return redirect(url_for("auth.login"))
    
    return render_template("forgot_password.html")

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        flash("Invalid or expired reset token.", "danger")
        return redirect(url_for("auth.forgot_password"))
    
    if request.method == "POST":
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("reset_password.html", token=token)
        
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("reset_password.html", token=token)
        
        # Update password
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        user.password = hashed_pw
        user.clear_reset_token()
        
        flash("Your password has been updated! You can now log in.", "success")
        return redirect(url_for("auth.login"))
    
    return render_template("reset_password.html", token=token)

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for("auth.login"))

# API Routes with JWT
@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=data['email'].lower()).first()
    
    if user and user.password and bcrypt.check_password_hash(user.password, data['password']):
        if not user.confirmed:
            return jsonify({'error': 'Please confirm your email first'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate JWT token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    
    if not data or not all(k in data for k in ('name', 'email', 'password')):
        return jsonify({'error': 'Name, email, and password required'}), 400
    
    if len(data['password']) < 8:
        return jsonify({'error': 'Password must be at least 8 characters long'}), 400
    
    email = data['email'].lower()
    
    # Check if user exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    # Create user
    hashed_pw = bcrypt.generate_password_hash(data['password']).decode("utf-8")
    user = User(name=data['name'], email=email, password=hashed_pw)
    db.session.add(user)
    db.session.commit()
    
    # Generate confirmation token
    s = generate_serializer()
    token = s.dumps(email, salt="email-confirm")
    
    # Send confirmation email
    try:
        send_confirmation_email(user, token)
        return jsonify({
            'message': 'User created successfully. Please check your email to confirm your account.',
            'user_id': user.id
        }), 201
    except Exception as e:
        return jsonify({
            'message': 'User created but email confirmation failed',
            'user_id': user.id
        }), 201

@auth_bp.route("/api/profile", methods=["GET"])
@jwt_required()
def api_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200
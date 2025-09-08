# Flask Blog Application

This is a full-featured **Flask blog application** with:

- User signup/login/logout system
- Profile page
- CRUD for posts and comments
- MySpace-inspired UI with HTML & CSS
- PostgreSQL database connection
- Blueprints structure (`auth`, `blog`)
- Environment variable support via `.env`
- Password hashing with Bcrypt
- Ready for deployment on Render

---

## 🚀 Features

- Users can sign up, log in, log out, and view their profile.
- Users can create, edit, and delete posts.
- Users can comment on posts.
- Responsive and retro-styled interface using CSS.
- Flash messages for user feedback.
- Modular structure using Flask Blueprints.

---

## 📂 File Structure

```
flask_blog/
├── app.py
├── extensions.py
├── auth/
│   ├── __init__.py
│   └── routes.py
├── blog/
│   ├── __init__.py
│   └── routes.py
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── signup.html
│   ├── login.html
│   ├── profile.html
│   ├── post_detail.html
│   └── create_post.html
├── static/
│   └── style.css
├── .env
└── requirements.txt
```

---

## ⚙️ Installation

1. Clone the repo:
   ```bash
   git clone <your-repo-url>
   cd flask_blog
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   venv\Scripts\activate      # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file with:
   ```
   APP_SECRET_KEY=your_secret_key
   DATABASE_URI=postgres://username:password@host:port/dbname
   ```

---

## 🏃 Running Locally

```bash
python app.py
# or for production testing
gunicorn app:app --bind 0.0.0.0:5000 --workers 4
```

Visit `http://127.0.0.1:5000` in your browser.

---

## 🌐 Deployment on Render

1. Push the code to GitHub.
2. Create a new Web Service on Render, connect to your repo.
3. Set Environment Variables on Render:
   - `APP_SECRET_KEY`
   - `DATABASE_URI`
4. Start Command: `gunicorn app:app`
5. Deploy!

---

## 📦 Dependencies

- Flask
- Flask-Bcrypt
- Flask-SQLAlchemy
- python-dotenv
- Gunicorn (for Linux/production)


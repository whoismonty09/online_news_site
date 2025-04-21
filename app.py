from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

# NewsAPI configuration
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
NEWS_API_URL = 'https://newsapi.org/v2/top-headlines'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    articles = db.relationship('Article', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Article {self.title}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def fetch_news(category=None, country='us'):
    """Fetch news from NewsAPI"""
    params = {
        'apiKey': NEWS_API_KEY,
        'country': country
    }
    
    if category:
        params['category'] = category
    
    try:
        response = requests.get(NEWS_API_URL, params=params)
        response.raise_for_status()
        return response.json()['articles']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return []

@app.route('/')
def home():
    """Home page route"""
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        if not username or not password:
            flash('Please fill in both username and password', 'error')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        
        login_user(user, remember=remember)
        flash('Logged in successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('signup'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating account. Please try again.', 'error')
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_articles = Article.query.filter_by(user_id=current_user.id).order_by(Article.created_at.desc()).all()
    return render_template('dashboard.html', articles=user_articles)

@app.route('/news')
def news():
    """News listing page route"""
    api_articles = fetch_news()
    local_articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('news.html', 
                         api_articles=api_articles, 
                         local_articles=local_articles)

@app.route('/categories')
def categories():
    """Category filter page route"""
    category = request.args.get('category', '')
    api_articles = fetch_news(category=category)
    local_articles = Article.query.filter_by(category=category).order_by(Article.created_at.desc()).all()
    return render_template('news.html', 
                         api_articles=api_articles, 
                         local_articles=local_articles,
                         selected_category=category)

@app.route('/publish', methods=['GET', 'POST'])
@login_required
def publish():
    """Publish new article route"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        image_url = request.form.get('image_url')

        if not all([title, content, category]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('publish'))

        article = Article(
            title=title,
            content=content,
            category=category,
            image_url=image_url,
            user_id=current_user.id
        )

        try:
            db.session.add(article)
            db.session.commit()
            flash('Article published successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error publishing article. Please try again.', 'error')
            return redirect(url_for('publish'))

    return render_template('publish.html')

# Create database tables and test user
with app.app_context():
    db.drop_all()  # Drop all existing tables
    db.create_all()  # Create new tables with updated schema
    
    # Create a test user if no users exist
    if User.query.count() == 0:
        test_user = User(
            username='test',
            email='test@example.com'
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        db.session.commit()
        print("Test user created with username: 'test' and password: 'test123'")

if __name__ == '__main__':
    app.run(debug=True) 
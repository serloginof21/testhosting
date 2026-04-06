import os  # 👈 ЭТА СТРОЧКА ДОЛЖНА БЫТЬ В САМОМ НАЧАЛЕ!
from datetime import datetime
from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# ===== НАСТРОЙКА БАЗЫ ДАННЫХ =====
# Получаем URL базы данных из переменной окружения
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # Render использует 'postgres://', меняем на 'postgresql://'
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print("✅ Используется PostgreSQL (облачная БД)")
else:
    # Для локальной разработки
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///TestPythonWebSite.db'
    print("⚠️ Используется SQLite (локальная БД)")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ===== ВАША МОДЕЛЬ (БЕЗ ИЗМЕНЕНИЙ) =====
class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    intro = db.Column(db.String(300), nullable=True)
    text = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Integer, nullable=True)
    views = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<Article %r>' % self.id


# ===== ВСЕ ВАШИ МАРШРУТЫ (ОСТАЮТСЯ ТЕ ЖЕ) =====
@app.route('/')
@app.route('/home')
def index():
    popular_articles = Article.query.order_by(Article.views.desc()).limit(3).all()
    recent_articles = Article.query.order_by(Article.date.desc()).limit(3).all()
    return render_template("index.html", popular_articles=popular_articles, recent_articles=recent_articles)


@app.route('/posts')
def posts():
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'date')

    if search_query:
        articles = Article.query.filter(
            (Article.title.contains(search_query)) |
            (Article.intro.contains(search_query))
        )
    else:
        articles = Article.query

    if sort_by == 'score':
        articles = articles.order_by(Article.score.desc().nullslast(), Article.date.desc())
    elif sort_by == 'views':
        articles = articles.order_by(Article.views.desc().nullslast(), Article.date.desc())
    else:
        articles = articles.order_by(Article.date.desc())

    articles = articles.all()
    return render_template("posts.html", articles=articles, search_query=search_query, sort_by=sort_by)


@app.route('/posts/<int:id>')
def posts_detail(id):
    article = Article.query.get(id)
    if article:
        article.views = (article.views or 0) + 1
        db.session.commit()
    popular_articles = Article.query.order_by(Article.views.desc()).limit(5).all()
    return render_template("post_detail.html", article=article, popular_articles=popular_articles)


@app.route('/posts/<int:id>/delete')
def posts_delete(id):
    article = Article.query.get_or_404(id)
    try:
        db.session.delete(article)
        db.session.commit()
        return redirect('/posts')
    except:
        return "При удалении статьи произошла ошибка"


@app.route('/posts/<int:id>/update', methods=['POST', 'GET'])
def posts_update(id):
    article = Article.query.get(id)
    if request.method == 'POST':
        article.title = request.form['title']
        article.intro = request.form['intro']
        article.text = request.form['text']
        article.score = request.form.get('score', type=int)
        try:
            db.session.commit()
            return redirect('/posts')
        except:
            return "При редактировании статьи произошла ошибка!"
    else:
        return render_template("post_update.html", article=article)


@app.route('/create-article', methods=['POST', 'GET'])
def create_article():
    if request.method == 'POST':
        title = request.form['title']
        intro = request.form['intro']
        text = request.form['text']
        score = request.form.get('score', type=int)
        article = Article(title=title, intro=intro, text=text, score=score)
        try:
            db.session.add(article)
            db.session.commit()
            return redirect('/posts')
        except:
            return "При добавлении статьи произошла ошибка!"
    else:
        return render_template("create-article.html")


# ===== ЗАПУСК (только для локальной разработки) =====
if __name__ == "__main__":
    app.run(debug=True)
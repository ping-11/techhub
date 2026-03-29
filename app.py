#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechHub - 科技爱好者论坛
Flask + SQLite 前后端完整应用
"""

import os
import hashlib
import secrets
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort, jsonify
)
import sqlite3

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
DB_PATH = os.path.join(os.path.dirname(__file__), 'forum.db')

# ─────────────────────────────────────────────
#  数据库辅助
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,
            email     TEXT UNIQUE NOT NULL,
            avatar    TEXT DEFAULT '🤖',
            bio       TEXT DEFAULT '',
            role      TEXT DEFAULT 'user',
            banned    INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS categories (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL,
            icon  TEXT NOT NULL,
            desc  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS posts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            content     TEXT NOT NULL,
            user_id     INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            views       INTEGER DEFAULT 0,
            pinned      INTEGER DEFAULT 0,
            locked      INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(category_id) REFERENCES categories(id)
        );

        CREATE TABLE IF NOT EXISTS replies (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            content    TEXT NOT NULL,
            user_id    INTEGER NOT NULL,
            post_id    INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(post_id) REFERENCES posts(id)
        );

        CREATE TABLE IF NOT EXISTS likes (
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            PRIMARY KEY(user_id, post_id)
        );
        """)
        # 初始化分类
        cats = db.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        if cats == 0:
            db.executemany(
                "INSERT INTO categories(name,icon,desc) VALUES(?,?,?)",
                [
                    ('编程技术', '💻', '语言、框架、算法，代码人的天堂'),
                    ('硬件数码', '🔧', '电脑配件、手机、外设评测'),
                    ('AI & 机器学习', '🤖', '大模型、深度学习、炼丹实践'),
                    ('开源项目', '🌐', '分享好玩的开源项目与工具'),
                    ('职场与成长', '🚀', '求职经验、技术路线、软技能'),
                    ('水吧闲聊', '☕', '科技相关的日常闲聊'),
                ]
            )
        # 初始管理员
        admin = db.execute("SELECT id FROM users WHERE username='admin'").fetchone()
        if not admin:
            db.execute(
                "INSERT INTO users(username,password,email,avatar,role) VALUES(?,?,?,?,?)",
                ('admin', hash_pw('admin123'), 'admin@techhub.dev', '👑', 'admin')
            )
        db.commit()


def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ─────────────────────────────────────────────
#  装饰器
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return wrapped


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if session.get('role') != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return wrapped


# ─────────────────────────────────────────────
#  模板上下文
# ─────────────────────────────────────────────

@app.context_processor
def inject_globals():
    db = get_db()
    categories = db.execute("SELECT * FROM categories").fetchall()
    user = None
    if 'user_id' in session:
        user = db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    db.close()
    return dict(categories=categories, current_user=user, now=datetime.now())


# ─────────────────────────────────────────────
#  首页
# ─────────────────────────────────────────────

@app.route('/')
def index():
    db = get_db()
    page = max(1, request.args.get('page', 1, type=int))
    cat_id = request.args.get('cat', type=int)
    search = request.args.get('q', '').strip()
    per_page = 15

    query = """
        SELECT p.*, u.username, u.avatar, c.name AS cat_name, c.icon AS cat_icon,
               (SELECT COUNT(*) FROM replies WHERE post_id=p.id) AS reply_count,
               (SELECT COUNT(*) FROM likes WHERE post_id=p.id) AS like_count
        FROM posts p
        JOIN users u ON p.user_id=u.id
        JOIN categories c ON p.category_id=c.id
        WHERE u.banned=0
    """
    params = []
    if cat_id:
        query += " AND p.category_id=?"
        params.append(cat_id)
    if search:
        query += " AND (p.title LIKE ? OR p.content LIKE ?)"
        params += [f'%{search}%', f'%{search}%']
    query += " ORDER BY p.pinned DESC, p.created_at DESC LIMIT ? OFFSET ?"

    total_q = "SELECT COUNT(*) FROM posts p JOIN users u ON p.user_id=u.id WHERE u.banned=0"
    total_p = []
    if cat_id:
        total_q += " AND p.category_id=?"
        total_p.append(cat_id)
    if search:
        total_q += " AND (p.title LIKE ? OR p.content LIKE ?)"
        total_p += [f'%{search}%', f'%{search}%']

    total = db.execute(total_q, total_p).fetchone()[0]
    posts = db.execute(query, params + [per_page, (page-1)*per_page]).fetchall()
    stats = db.execute("""
        SELECT
          (SELECT COUNT(*) FROM users) AS user_count,
          (SELECT COUNT(*) FROM posts) AS post_count,
          (SELECT COUNT(*) FROM replies) AS reply_count
    """).fetchone()
    hot_posts = db.execute("""
        SELECT p.id, p.title, p.views,
               (SELECT COUNT(*) FROM replies WHERE post_id=p.id) AS rc
        FROM posts p JOIN users u ON p.user_id=u.id
        WHERE u.banned=0
        ORDER BY p.views DESC LIMIT 5
    """).fetchall()
    db.close()
    total_pages = (total + per_page - 1) // per_page
    return render_template('index.html',
        posts=posts, page=page, total_pages=total_pages,
        cat_id=cat_id, search=search, stats=stats, hot_posts=hot_posts)


# ─────────────────────────────────────────────
#  帖子详情
# ─────────────────────────────────────────────

@app.route('/post/<int:pid>')
def post_detail(pid):
    db = get_db()
    post = db.execute("""
        SELECT p.*, u.username, u.avatar, u.bio, c.name AS cat_name
        FROM posts p JOIN users u ON p.user_id=u.id
        JOIN categories c ON p.category_id=c.id
        WHERE p.id=?
    """, (pid,)).fetchone()
    if not post:
        abort(404)
    db.execute("UPDATE posts SET views=views+1 WHERE id=?", (pid,))
    db.commit()
    replies = db.execute("""
        SELECT r.*, u.username, u.avatar
        FROM replies r JOIN users u ON r.user_id=u.id
        WHERE r.post_id=? ORDER BY r.created_at ASC
    """, (pid,)).fetchall()
    like_count = db.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (pid,)).fetchone()[0]
    liked = False
    if 'user_id' in session:
        liked = db.execute("SELECT 1 FROM likes WHERE user_id=? AND post_id=?",
                           (session['user_id'], pid)).fetchone() is not None
    db.close()
    return render_template('post.html', post=post, replies=replies,
                           like_count=like_count, liked=liked)


# ─────────────────────────────────────────────
#  发帖
# ─────────────────────────────────────────────

@app.route('/new-post', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        cat_id = request.form.get('category', type=int)
        if not title or not content or not cat_id:
            flash('标题、内容、分类不能为空', 'danger')
            return redirect(url_for('new_post'))
        db = get_db()
        db.execute("INSERT INTO posts(title,content,user_id,category_id) VALUES(?,?,?,?)",
                   (title, content, session['user_id'], cat_id))
        db.commit()
        pid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.close()
        flash('发帖成功！', 'success')
        return redirect(url_for('post_detail', pid=pid))
    return render_template('new_post.html')


# ─────────────────────────────────────────────
#  回复
# ─────────────────────────────────────────────

@app.route('/reply/<int:pid>', methods=['POST'])
@login_required
def reply(pid):
    content = request.form.get('content', '').strip()
    if not content:
        flash('回复不能为空', 'danger')
        return redirect(url_for('post_detail', pid=pid))
    db = get_db()
    post = db.execute("SELECT locked FROM posts WHERE id=?", (pid,)).fetchone()
    if not post:
        abort(404)
    if post['locked'] and session.get('role') != 'admin':
        flash('帖子已锁定，无法回复', 'warning')
        return redirect(url_for('post_detail', pid=pid))
    db.execute("INSERT INTO replies(content,user_id,post_id) VALUES(?,?,?)",
               (content, session['user_id'], pid))
    db.commit()
    db.close()
    flash('回复成功', 'success')
    return redirect(url_for('post_detail', pid=pid) + '#replies')


# ─────────────────────────────────────────────
#  点赞 (AJAX)
# ─────────────────────────────────────────────

@app.route('/like/<int:pid>', methods=['POST'])
@login_required
def like_post(pid):
    db = get_db()
    exists = db.execute("SELECT 1 FROM likes WHERE user_id=? AND post_id=?",
                        (session['user_id'], pid)).fetchone()
    if exists:
        db.execute("DELETE FROM likes WHERE user_id=? AND post_id=?",
                   (session['user_id'], pid))
        liked = False
    else:
        db.execute("INSERT INTO likes(user_id,post_id) VALUES(?,?)",
                   (session['user_id'], pid))
        liked = True
    db.commit()
    count = db.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (pid,)).fetchone()[0]
    db.close()
    return jsonify({'liked': liked, 'count': count})


# ─────────────────────────────────────────────
#  用户认证
# ─────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        if not username or not email or not password:
            flash('所有字段均为必填', 'danger')
            return redirect(url_for('register'))
        if password != confirm:
            flash('两次密码不一致', 'danger')
            return redirect(url_for('register'))
        if len(password) < 6:
            flash('密码至少6位', 'danger')
            return redirect(url_for('register'))
        db = get_db()
        try:
            db.execute("INSERT INTO users(username,password,email) VALUES(?,?,?)",
                       (username, hash_pw(password), email))
            db.commit()
            user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f'欢迎加入 TechHub，{username}！', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('用户名或邮箱已被注册', 'danger')
        finally:
            db.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        db.close()
        if user and user['password'] == hash_pw(password):
            if user['banned']:
                flash('账号已被封禁，请联系管理员', 'danger')
                return redirect(url_for('login'))
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f'欢迎回来，{username}！', 'success')
            next_url = request.args.get('next') or url_for('index')
            return redirect(next_url)
        flash('用户名或密码错误', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('已退出登录', 'info')
    return redirect(url_for('index'))


# ─────────────────────────────────────────────
#  用户页面
# ─────────────────────────────────────────────

@app.route('/user/<username>')
def user_profile(username):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not user:
        abort(404)
    posts = db.execute("""
        SELECT p.*, c.name AS cat_name, c.icon AS cat_icon,
               (SELECT COUNT(*) FROM replies WHERE post_id=p.id) AS reply_count
        FROM posts p JOIN categories c ON p.category_id=c.id
        WHERE p.user_id=? ORDER BY p.created_at DESC LIMIT 20
    """, (user['id'],)).fetchall()
    reply_count = db.execute("SELECT COUNT(*) FROM replies WHERE user_id=?", (user['id'],)).fetchone()[0]
    db.close()
    return render_template('profile.html', profile_user=user, posts=posts, reply_count=reply_count)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    if request.method == 'POST':
        bio = request.form.get('bio', '').strip()[:200]
        avatar = request.form.get('avatar', '🤖').strip()
        new_pw = request.form.get('new_password', '')
        if new_pw:
            old_pw = request.form.get('old_password', '')
            if user['password'] != hash_pw(old_pw):
                flash('原密码错误', 'danger')
                db.close()
                return redirect(url_for('settings'))
            if len(new_pw) < 6:
                flash('新密码至少6位', 'danger')
                db.close()
                return redirect(url_for('settings'))
            db.execute("UPDATE users SET bio=?,avatar=?,password=? WHERE id=?",
                       (bio, avatar, hash_pw(new_pw), session['user_id']))
        else:
            db.execute("UPDATE users SET bio=?,avatar=? WHERE id=?",
                       (bio, avatar, session['user_id']))
        db.commit()
        db.close()
        flash('设置已保存', 'success')
        return redirect(url_for('settings'))
    db.close()
    return render_template('settings.html', user=user)


# ─────────────────────────────────────────────
#  管理员页面
# ─────────────────────────────────────────────

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    db = get_db()
    stats = db.execute("""
        SELECT
          (SELECT COUNT(*) FROM users) AS user_count,
          (SELECT COUNT(*) FROM posts) AS post_count,
          (SELECT COUNT(*) FROM replies) AS reply_count,
          (SELECT COUNT(*) FROM users WHERE banned=1) AS banned_count
    """).fetchone()
    recent_users = db.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 10").fetchall()
    recent_posts = db.execute("""
        SELECT p.*, u.username FROM posts p JOIN users u ON p.user_id=u.id
        ORDER BY p.created_at DESC LIMIT 10
    """).fetchall()
    db.close()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_users=recent_users, recent_posts=recent_posts)


@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    db = get_db()
    search = request.args.get('q', '').strip()
    if search:
        users = db.execute(
            "SELECT * FROM users WHERE username LIKE ? OR email LIKE ? ORDER BY id DESC",
            (f'%{search}%', f'%{search}%')
        ).fetchall()
    else:
        users = db.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    db.close()
    return render_template('admin/users.html', users=users, search=search)


@app.route('/admin/user/<int:uid>/ban', methods=['POST'])
@login_required
@admin_required
def admin_ban(uid):
    if uid == session['user_id']:
        flash('不能封禁自己', 'danger')
        return redirect(url_for('admin_users'))
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    new_state = 0 if user['banned'] else 1
    db.execute("UPDATE users SET banned=? WHERE id=?", (new_state, uid))
    db.commit()
    db.close()
    flash(f"用户 {user['username']} 已{'封禁' if new_state else '解封'}", 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/posts')
@login_required
@admin_required
def admin_posts():
    db = get_db()
    posts = db.execute("""
        SELECT p.*, u.username, c.name AS cat_name
        FROM posts p JOIN users u ON p.user_id=u.id
        JOIN categories c ON p.category_id=c.id
        ORDER BY p.created_at DESC
    """).fetchall()
    db.close()
    return render_template('admin/posts.html', posts=posts)


@app.route('/admin/post/<int:pid>/pin', methods=['POST'])
@login_required
@admin_required
def admin_pin(pid):
    db = get_db()
    post = db.execute("SELECT pinned FROM posts WHERE id=?", (pid,)).fetchone()
    db.execute("UPDATE posts SET pinned=? WHERE id=?", (0 if post['pinned'] else 1, pid))
    db.commit()
    db.close()
    return redirect(url_for('admin_posts'))


@app.route('/admin/post/<int:pid>/lock', methods=['POST'])
@login_required
@admin_required
def admin_lock(pid):
    db = get_db()
    post = db.execute("SELECT locked FROM posts WHERE id=?", (pid,)).fetchone()
    db.execute("UPDATE posts SET locked=? WHERE id=?", (0 if post['locked'] else 1, pid))
    db.commit()
    db.close()
    return redirect(url_for('admin_posts'))


@app.route('/admin/post/<int:pid>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_post(pid):
    db = get_db()
    db.execute("DELETE FROM replies WHERE post_id=?", (pid,))
    db.execute("DELETE FROM likes WHERE post_id=?", (pid,))
    db.execute("DELETE FROM posts WHERE id=?", (pid,))
    db.commit()
    db.close()
    flash('帖子已删除', 'success')
    return redirect(url_for('admin_posts'))


# ─────────────────────────────────────────────
#  错误页
# ─────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, msg='页面不存在'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', code=403, msg='无权访问'), 403


# ─────────────────────────────────────────────
#  启动
# ─────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("  TechHub 论坛已启动")
    print("  访问: http://127.0.0.1:5000")
    print("  管理员账号: admin / admin123")
    print("=" * 50)
    app.run(debug=True, port=5000)

# 付録E 通し課題の完成コード

ここに載せるのは、`shared/running-example.md` の確定仕様どおりに、Phase 4〜8の手順を実際に1行ずつ実行して動かしたReadLogのコードだ。機能一覧の8項目（ユーザー登録・ログイン・ログアウト・本の登録・一覧表示・詳細表示・編集・削除）と、第4部の安全編10項目のうち項目7（通信）を除く9項目を、実機で確認済みだ。コピーして使える。

## フォルダ構成

Phase 4で決めたフォルダ構成に、Phase 5で機能を積み上げた結果、最終的に次の形になった。

```
readlog/
  package.json
  package-lock.json
  .gitignore
  .env.example
  src/
    app.js              画面・処理の入口
    db/
      index.js           データベース接続とテーブル定義
    routes/
      auth.js             ユーザー登録・ログイン・ログアウト
      books.js            本の登録・一覧・詳細・編集・削除
    views/
      register.ejs        新規登録画面
      login.ejs            ログイン画面
      books/
        index.ejs          本の一覧画面
        form.ejs            本の登録・編集画面
        show.ejs            本の詳細画面
```

## 起動方法

手元で動かすには、次の手順を踏む。

1. `readlog/` フォルダの中で `npm install` を実行し、ライブラリを導入する
2. `.env.example` をコピーして `.env` を作り、`SESSION_SECRET` に好きな文字列を入れる
3. `node src/app.js` で起動する
4. ブラウザで `http://localhost:3000` を開く

## package.json

導入したライブラリは、Express・SQLiteを扱うbetter-sqlite3・セッション管理のexpress-session・パスワードをハッシュ化するbcrypt・テンプレートエンジンのEJS・環境変数を読み込むdotenvの6つだ。

```json
{
  "name": "readlog",
  "version": "1.0.0",
  "description": "読んだ本のタイトルと感想、読了日を記録するアプリ",
  "main": "src/app.js",
  "scripts": {
    "start": "node src/app.js"
  },
  "dependencies": {
    "bcrypt": "^6.0.0",
    "better-sqlite3": "^13.0.3",
    "dotenv": "^17.4.2",
    "ejs": "^6.0.1",
    "express": "^5.2.1",
    "express-session": "^1.19.0"
  }
}
```

## .gitignore

`node_modules`・秘密情報を含む`.env`・データベースファイルをGitの記録対象から外す。

```
node_modules/
.env
*.sqlite
```

## .env.example

必要な環境変数は、セッションの署名に使う値の1つだけだ。

```
SESSION_SECRET=
```

## src/app.js

画面・処理の入口。Phase 4で`.env`の読み込みをファイルの一番先頭に置いた。Phase 7で、エラーの詳細を画面に出さずログにだけ残す処理を末尾に追加した。

```javascript
require('dotenv').config();

const path = require('path');
const express = require('express');
const session = require('express-session');

const authRoutes = require('./routes/auth');
const bookRoutes = require('./routes/books');

const app = express();
const PORT = process.env.PORT || 3000;

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.use(express.urlencoded({ extended: true }));
app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
}));

app.use('/', authRoutes);
app.use('/books', bookRoutes);

app.get('/', (req, res) => {
  res.redirect('/login');
});

// 第4部4-8：エラーの詳細はユーザー画面に出さず、開発者だけが見られるログに残す
app.use((err, req, res, next) => {
  console.error(err);
  res.status(err.status || 500).send('エラーが発生しました。');
});

app.listen(PORT, () => {
  console.log(`ReadLog listening on http://localhost:${PORT}`);
});
```

## src/db/index.js

`shared/running-example.md`のデータ構造どおり、`users`と`books`の2つのテーブルを作る。

```javascript
const path = require('path');
const Database = require('better-sqlite3');

const db = new Database(path.join(__dirname, '../../readlog.sqlite'));

db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    review TEXT,
    finished_on TEXT,
    status TEXT NOT NULL DEFAULT '未読',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
  );
`);

module.exports = db;
```

## src/routes/auth.js

ユーザー登録・ログイン・ログアウトを担当する。パスワードはPhase 4で導入したハッシュ化を使い、平文では保存しない。

```javascript
const express = require('express');
const bcrypt = require('bcrypt');
const db = require('../db');

const router = express.Router();

// 新規登録画面
router.get('/register', (req, res) => {
  res.render('register', { error: null });
});

// ユーザー登録
router.post('/register', async (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).render('register', { error: 'メールアドレスとパスワードを入力してください。' });
  }

  const existing = db.prepare('SELECT id FROM users WHERE email = ?').get(email);
  if (existing) {
    return res.status(400).render('register', { error: 'そのメールアドレスはすでに登録されています。' });
  }

  const passwordHash = await bcrypt.hash(password, 10);
  db.prepare('INSERT INTO users (email, password_hash) VALUES (?, ?)').run(email, passwordHash);

  res.redirect('/login');
});

// ログイン画面
router.get('/login', (req, res) => {
  res.render('login', { error: null });
});

// ログイン
router.post('/login', async (req, res) => {
  const { email, password } = req.body;

  const user = db.prepare('SELECT id, password_hash FROM users WHERE email = ?').get(email);
  if (!user) {
    return res.status(401).render('login', { error: 'メールアドレスまたはパスワードが違います。' });
  }

  const ok = await bcrypt.compare(password, user.password_hash);
  if (!ok) {
    return res.status(401).render('login', { error: 'メールアドレスまたはパスワードが違います。' });
  }

  req.session.userId = user.id;
  res.redirect('/books');
});

// ログアウト
router.post('/logout', (req, res) => {
  req.session.destroy(() => {
    res.redirect('/login');
  });
});

module.exports = router;
```

## src/routes/books.js

本の登録・一覧・詳細・編集・削除を担当する。第4部4-2の入力検証と、4-6の持ち主確認を、Phase 7でここに追加した。

```javascript
const express = require('express');
const db = require('../db');

const router = express.Router();

function requireLogin(req, res, next) {
  if (!req.session.userId) {
    return res.redirect('/login');
  }
  next();
}

router.use(requireLogin);

// 第4部4-2：型・必須かどうか・文字数の上限を検証する（Phase 3のデータ構造の表に対応）
const STATUSES = ['未読', '読書中', '読了'];
function validateBook(body) {
  const { title, author, review, finished_on, status } = body;

  if (!title || !title.trim()) return 'タイトルを入力してください。';
  if (title.length > 200) return 'タイトルは200文字以内で入力してください。';
  if (author && author.length > 100) return '著者は100文字以内で入力してください。';
  if (review && review.length > 5000) return '感想は5000文字以内で入力してください。';
  if (finished_on && !/^\d{4}-\d{2}-\d{2}$/.test(finished_on)) return '読了日はYYYY-MM-DD形式で入力してください。';
  if (status && !STATUSES.includes(status)) return 'ステータスの値が不正です。';

  return null;
}

// 一覧表示（読了日順）
router.get('/', (req, res) => {
  const books = db
    .prepare('SELECT * FROM books WHERE user_id = ? ORDER BY finished_on DESC')
    .all(req.session.userId);
  res.render('books/index', { books });
});

// 登録画面
router.get('/new', (req, res) => {
  res.render('books/form', { book: null, error: null });
});

// 登録
router.post('/', (req, res) => {
  const error = validateBook(req.body);
  if (error) {
    return res.status(400).render('books/form', { book: req.body, error });
  }

  const { title, author, review, finished_on, status } = req.body;
  db.prepare(
    'INSERT INTO books (user_id, title, author, review, finished_on, status) VALUES (?, ?, ?, ?, ?, ?)'
  ).run(req.session.userId, title, author || null, review || null, finished_on || null, status || '未読');

  res.redirect('/books');
});

// 第4部4-6：操作の対象が、ログイン中の利用者自身のデータかどうかを確認する
function findOwnBook(req, res) {
  const book = db.prepare('SELECT * FROM books WHERE id = ?').get(req.params.id);
  if (!book || book.user_id !== req.session.userId) {
    res.status(404).send('本が見つかりません。');
    return null;
  }
  return book;
}

// 詳細表示（感想を表示）
router.get('/:id', (req, res) => {
  const book = findOwnBook(req, res);
  if (!book) return;
  res.render('books/show', { book });
});

// 編集画面
router.get('/:id/edit', (req, res) => {
  const book = findOwnBook(req, res);
  if (!book) return;
  res.render('books/form', { book, error: null });
});

// 編集
router.post('/:id/edit', (req, res) => {
  const book = findOwnBook(req, res);
  if (!book) return;

  const error = validateBook(req.body);
  if (error) {
    return res.status(400).render('books/form', { book: { ...book, ...req.body }, error });
  }

  const { title, author, review, finished_on, status } = req.body;
  db.prepare(
    'UPDATE books SET title = ?, author = ?, review = ?, finished_on = ?, status = ? WHERE id = ?'
  ).run(title, author || null, review || null, finished_on || null, status || '未読', book.id);

  res.redirect(`/books/${book.id}`);
});

// 削除
router.post('/:id/delete', (req, res) => {
  const book = findOwnBook(req, res);
  if (!book) return;

  db.prepare('DELETE FROM books WHERE id = ?').run(book.id);
  res.redirect('/books');
});

module.exports = router;
```

## src/views/register.ejs

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>新規登録 - ReadLog</title>
</head>
<body>
  <h1>新規登録</h1>
  <% if (error) { %>
    <p style="color: red;"><%= error %></p>
  <% } %>
  <form method="POST" action="/register">
    <label>メールアドレス <input type="email" name="email" required></label><br>
    <label>パスワード <input type="password" name="password" required></label><br>
    <button type="submit">登録する</button>
  </form>
  <p><a href="/login">ログインはこちら</a></p>
</body>
</html>
```

## src/views/login.ejs

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>ログイン - ReadLog</title>
</head>
<body>
  <h1>ログイン</h1>
  <% if (error) { %>
    <p style="color: red;"><%= error %></p>
  <% } %>
  <form method="POST" action="/login">
    <label>メールアドレス <input type="email" name="email" required></label><br>
    <label>パスワード <input type="password" name="password" required></label><br>
    <button type="submit">ログイン</button>
  </form>
  <p><a href="/register">新規登録はこちら</a></p>
</body>
</html>
```

## src/views/books/index.ejs

一覧の各項目は、EJSの`<%= %>`で出力する。入力された文字列がそのままHTMLとして実行されないよう、自動でエスケープされる（第4部4-4）。

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>本の一覧 - ReadLog</title>
</head>
<body>
  <h1>本の一覧</h1>
  <p><a href="/books/new">本を登録する</a></p>
  <ul>
    <% books.forEach(function(book) { %>
      <li>
        <a href="/books/<%= book.id %>"><%= book.title %></a>
        （<%= book.status %> / <%= book.finished_on || '未読了' %>）
      </li>
    <% }) %>
  </ul>
  <form method="POST" action="/logout"><button type="submit">ログアウト</button></form>
</body>
</html>
```

## src/views/books/form.ejs

本の登録と編集で、同じ画面を使い回す。

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title><%= book ? '本を編集' : '本を登録' %> - ReadLog</title>
</head>
<body>
  <h1><%= book ? '本を編集' : '本を登録' %></h1>
  <% if (error) { %>
    <p style="color: red;"><%= error %></p>
  <% } %>
  <form method="POST" action="<%= book && book.id ? '/books/' + book.id + '/edit' : '/books' %>">
    <label>タイトル <input type="text" name="title" value="<%= book ? (book.title || '') : '' %>" required></label><br>
    <label>著者 <input type="text" name="author" value="<%= book ? (book.author || '') : '' %>"></label><br>
    <label>感想 <textarea name="review"><%= book ? (book.review || '') : '' %></textarea></label><br>
    <label>読了日 <input type="date" name="finished_on" value="<%= book ? (book.finished_on || '') : '' %>"></label><br>
    <label>ステータス
      <select name="status">
        <% ['未読', '読書中', '読了'].forEach(function(s) { %>
          <option value="<%= s %>" <%= book && book.status === s ? 'selected' : '' %>><%= s %></option>
        <% }) %>
      </select>
    </label><br>
    <button type="submit">保存する</button>
  </form>
</body>
</html>
```

## src/views/books/show.ejs

感想を表示する詳細画面。

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title><%= book.title %> - ReadLog</title>
</head>
<body>
  <h1><%= book.title %></h1>
  <p>著者：<%= book.author || '（未入力）' %></p>
  <p>ステータス：<%= book.status %></p>
  <p>読了日：<%= book.finished_on || '（未読了）' %></p>
  <p>感想：<%= book.review || '（未入力）' %></p>
  <p>
    <a href="/books/<%= book.id %>/edit">編集する</a>
    <form method="POST" action="/books/<%= book.id %>/delete" style="display:inline">
      <button type="submit">削除する</button>
    </form>
  </p>
  <p><a href="/books">一覧に戻る</a></p>
</body>
</html>
```

## 確認できなかった項目

第4部の項目7（通信）は、Phase 8で公開先URLを確認して初めて点検が終わる項目であり、このコード単体では点検できない。Phase 8の手順6に沿って、公開後にURLが`https://`で始まっていることを確認する。

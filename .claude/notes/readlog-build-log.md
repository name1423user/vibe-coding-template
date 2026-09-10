# ReadLog 実装ログ（付録D素材）

作業ディレクトリ: `scratchpad/readlog`（本リポジトリとは別のまっさらなディレクトリ）
実行環境: Node v22.22.2 / npm 10.9.7

## Phase 4 環境を作る

### 手順1 フォルダ作成・Git初期化
```
mkdir readlog && cd readlog
git init
```
エラーなし。

### 手順2 ライブラリ導入
本文どおり、Express・SQLiteライブラリ・セッション管理ライブラリ・パスワードハッシュ化ライブラリ・EJSを導入。
```
npm install express better-sqlite3 express-session bcrypt ejs
```
結果：`added 81 packages`。エラーなし。native binding（better-sqlite3, bcrypt）のビルド失敗もなし（prebuildが使われた）。

導入されたバージョン：
- express 5.2.1（Express 5系。本文はバージョンを指定していない）
- better-sqlite3 13.0.3
- express-session 1.19.0
- bcrypt 6.0.0
- ejs 6.0.1

備考：本文の手順2は「必要なライブラリを導入する」から始まり、その前に `npm init` は書かれていない。
`npm install <パッケージ名>` を package.json が存在しないフォルダで実行すると、npm 10系は自動で最小限の
package.json を生成する（`name`・`version` フィールドなし）ため、これ自体は詰まりにはならなかった。
ただし生成される package.json は素っ気ないため、`name`・`version`・`scripts.start` は手動で補った
（本文に書かれた手順ではなく、著者としての補足）。

### 手順3 起動するだけの最小コード
`src/app.js` を作成し、`node src/app.js` で起動確認。
```
node src/app.js
→ ReadLog listening on http://localhost:3000
curl http://localhost:3000/
→ status=200 / "ReadLog is running."
```
エラーなし。

### 手順4・5 秘密情報の置き場所、.gitignore / .env.example、コミット
`.gitignore`（node_modules/ .env *.sqlite）と `.env.example`（`SESSION_SECRET=`）を作成し、コミット。
エラーなし。

```
git commit -m "Phase 4: 起動するだけの空のアプリ"
→ [master (root-commit) fca7fcc] 5 files changed, 1070 insertions(+)
```

Phase 4は最後まで詰まりなく完了した。

---

## Phase 5 実装する（1つ目の機能：ユーザー登録・ログイン・ログアウト）

機能一覧の並び（ユーザー登録→ログイン→ログアウト→本の登録…）どおり、認証まわりを1本目として実装。

- `src/db/index.js`：`shared/running-example.md` のデータ構造どおり `users` `books` テーブルを作成
- `src/routes/auth.js`：GET/POST `/register`、GET/POST `/login`、POST `/logout`
- `src/views/register.ejs`, `src/views/login.ejs`
- `src/app.js`：EJSをview engineに設定、`express.urlencoded`、`express-session`（`secret: process.env.SESSION_SECRET`）、ルーティングを追加

Phase 4の指示（秘密情報は環境変数として扱う）に従い、`.env` に実際の値を書いた。

```
echo "SESSION_SECRET=a-random-secret-string-chosen-by-the-reader" > .env
```

### 起動（本文Phase 4手順3で示された方法のまま）

```
node src/app.js
```

**stdout/stderr:**
```
Thu, 10 Sep 2026 06:30:44 GMT express-session deprecated req.secret; provide secret option at src/app.js:14:9
ReadLog listening on http://localhost:3000
```

プロセスは起動する（クラッシュしない）。しかし `secret` に警告が出ている。

### `/login` にアクセス

```
curl -i http://localhost:3000/login
```

**レスポンス：`500 Internal Server Error`**

```
Error: secret option required for sessions
    at session (node_modules/express-session/index.js:211:12)
    at Layer.handleRequest (node_modules/router/lib/layer.js:152:17)
    at trimPrefix (node_modules/router/index.js:342:13)
    at node_modules/router/index.js:297:9
    at processParams (node_modules/router/index.js:582:12)
    at next (node_modules/router/index.js:291:5)
    at read (node_modules/body-parser/lib/read.js:53:5)
    at urlencodedParser (node_modules/body-parser/lib/types/urlencoded.js:51:5)
    at Layer.handleRequest (node_modules/router/lib/layer.js:152:17)
    at trimPrefix (node_modules/router/index.js:342:13)
```

### 原因の切り分け

```
node -e "console.log(process.env.SESSION_SECRET)"
→ undefined
```

`.env` に値を書いても、プレーンな `node src/app.js` では `process.env` に反映されない。
Node は `.env` ファイルを自動では読み込まない。Node 20以降にある `--env-file` フラグを明示的に付けた場合のみ読み込む。

```
node --env-file=.env -e "console.log(process.env.SESSION_SECRET)"
→ a-random-secret-string-chosen-by-the-reader
```

### 本文側の該当箇所を確認

`manuscript/`・`shared/`・`outline.md` 全体を検索したが、`.env` の値を実際に読み込む方法
（`dotenv` ライブラリの導入、または `node --env-file` の使用）についての記述は一つもなかった。

- Phase 4 手順2「必要なライブラリを導入する」に挙がっているのは Express・SQLiteライブラリ・
  セッション管理ライブラリ・パスワードハッシュ化ライブラリ・EJSの5つのみで、`.env` 読み込み用の
  ライブラリは含まれていない
- Phase 4 手順4は「秘密情報は環境変数として扱う」と述べるのみで、ローカル実行時に `.env` を
  どう読ませるかには触れていない
- `.env.example` の説明（手順5の後の段落）も、値の埋め方は説明するが読み込み方法には触れない

**結論**：本文の手順を上から順にそのまま実行すると、最初にセッションを使う画面（`/login`）で
`500 Internal Server Error` が発生し、先に進めない。これはコード側の実装ミスではなく、
本文（Phase 4）に「`.env` の値をどうやってNodeプロセスに読み込ませるか」の説明が欠けていることが原因。

---

## Phase 4 修正後の再確認

本文にdotenvの読み込み手順を追加後、同じ手順で再実行。

```
npm install dotenv
```
→ エラーなし。`app.js` の一番先頭に `require('dotenv').config()` を追加。

```
node src/app.js
→ ◇ injected env (1) from .env
→ ReadLog listening on http://localhost:3000

curl -i http://localhost:3000/login
→ 200 OK
```

`secret option required for sessions` は解消。ここから先に進めた。

## Phase 5 実装する（続き：本の登録・一覧・詳細・編集・削除）

`src/routes/books.js`、`src/views/books/*.ejs` を作成し、`/books` 配下にマウント。
ログイン必須（`requireLogin`ミドルウェア）、一覧は`WHERE user_id = ?`で自分の本だけに絞った。

**注記**：詳細・編集・削除では、本文Phase 5の手順に「持ち主の確認」という指示がないため、
あえて持ち主チェックを入れずに実装した（Phase 6で見つかり、Phase 7で直す不具合として
本文が想定しているとおりの状態を再現するため）。

### 機能一覧8項目の動作確認（すべて同一プロセス内・Cookieでセッション維持）

| # | 機能 | 確認方法 | 結果 |
|---|---|---|---|
| 1 | ユーザー登録 | `POST /register` | 302、DBに`password_hash`がbcryptハッシュで保存されることを確認 |
| 2 | ログイン | `POST /login`（正しいPW／誤ったPW） | 正: 302→`/books`、誤: 401 |
| 3 | ログアウト | `POST /logout` | 302→`/login` |
| 4 | 本の登録 | `POST /books` | 302→`/books`、一覧に反映 |
| 5 | 一覧表示 | `GET /books` | 登録した本が表示される |
| 6 | 詳細表示 | `GET /books/:id` | タイトル・著者・感想・読了日・ステータスが表示される |
| 7 | 編集 | `POST /books/:id/edit` | 302、詳細画面に反映される |
| 8 | 削除 | `POST /books/:id/delete` | 302、一覧から消える |

8項目すべて動作を確認した。エラーなし。

### Phase 6が想定する異常系・極端な入力を先に試した結果（メモ）

Phase 6の本文で名指しされている3パターンを、Phase 5の実装のまま試した。

1. **タイトルを空で登録**（異常系）→ `400`、「タイトルを入力してください。」を表示。想定どおり弾かれた。
2. **他のユーザーの本のURLに直接アクセス**（異常系）→ userBのセッションで `/books/1`（userAの本）にアクセスすると、`200`でAさんの本の詳細がそのまま見えた。**本文が「Phase 6で見つかる」と書いている不具合が、実際にそのとおり再現した。** 持ち主チェックを入れていないので当然の結果であり、これは本文の欠落ではない。Phase 7の項目6（権限）で直す想定どおり。
3. **感想欄に非常に長い文章**（極端な入力）→ 20,000字を送ると `413 Payload Too Large`（`PayloadTooLargeError: request entity too large`、body-parserの既定上限）で落ちた。現実的な長さ（3,000字）では問題なく登録できた。20,000字は上限（既定100kb）を超えた場合の話であり、機能一覧の動作確認自体は妨げていない。ただしエラー画面にスタックトレースがそのまま出ており、第4部4-8（エラー表示）の観点では課題が残る。Phase 6・7で扱う話として記録しておく。

Phase 4・Phase 5の範囲では、これ以上の「詰まり」（先に進めなくなる本文側の欠落）は発生しなかった。

---

## Phase 6 動作を確かめる

本文の手順1〜6を実施。8機能すべての正常系、複数の異常系、極端な入力を試した。

### 正常系（8機能）

全機能、想定どおりのステータスコードで動作した（登録・編集・削除は302、一覧・詳細は200、
存在しないメールでのログインは401、メール重複登録は400、存在しないIDへのアクセスは404）。

### バグ報告1：他のユーザーの本のURLに直接アクセスすると、感想まで見えてしまう

- **期待した動作**：ログイン中の利用者が持ち主でない本にアクセスすると、閲覧できない
- **実際の動作**：`200 OK`でそのまま詳細（感想含む）が返ってくる
- **再現手順**：
  1. userA でログインし、本を1件登録する（id=1とする）
  2. userB でログインする
  3. userBのセッションで `GET /books/1` にアクセスする
  4. userAの本の詳細（感想含む）がそのまま表示される

本文の手順6の例外規定（権限に関わる不具合はPhase 5に戻らずPhase 7でまとめて扱う）に従い、
その場では直さず記録のみ行った。

### バグ報告2：感想欄に非常に長い文章を入れると、生のスタックトレースが画面に表示される

- **期待した動作**：長すぎる入力はエラーメッセージで弾かれる、または適切に処理される
- **実際の動作**：`413 Payload Too Large`とともに、ファイルパスを含む生のスタックトレースが
  HTMLでそのまま返ってくる（`PayloadTooLargeError: request entity too large` + `node_modules`配下の
  絶対パスを含むコールスタック）
- **再現手順**：
  1. ログインする
  2. `POST /books` で `review` に20,000字の文字列を送る
  3. レスポンスに `PayloadTooLargeError` のスタックトレースがそのまま含まれる

**本文の該当箇所を確認した結果**：Phase 6のReadLogの例では「極端な入力（感想欄に非常に長い文章を入れる）」
を試したと書かれているが、そこで何が見つかったかは書かれていない（異常系の権限バグは
「見つかった」と明記されているのに対し、極端な入力側は結果が書かれないまま次に進む）。
Phase 7のReadLog実例も、項目6（権限）にしか触れておらず、項目8（エラー表示）・項目2（入力の検証）に
対応する具体例がない。**これは本文の欠落と判断した。**
（第4部4-8の記述自体（「エラーの詳細をユーザー画面に出さない」）は、この不具合を正しく言い当てる
内容になっている。チェックリストの文言自体は機能している。欠けているのは、ReadLogの実例でこの不具合が
見つかったことを本文が書いていない点）

---

## Phase 7 安全を点検する

10項目を1つずつ、実際のReadLogに当てはめて点検した。

| # | 項目 | 点検方法 | 結果 |
|---|---|---|---|
| 1 | 秘密情報 | `git log --all --full-history -- .env`、コード内`grep`で値の直書きを検索 | 問題なし（`.env`は一度もコミットされていない、コードは`process.env`経由のみ） |
| 2 | 入力の検証 | タイトル201文字、不正なステータス値、不正な日付形式を送信 | **不具合あり → 修正**（`validateBook`関数を追加し、型・文字数上限・許容値を検証） |
| 3 | データベース操作 | 全クエリを`grep`で確認 | 問題なし（すべて`?`プレースホルダ、文字列連結なし） |
| 4 | 画面への出力 | `<script>alert(1)</script>`を感想に入れて表示を確認 | 問題なし（EJSの`<%= %>`が`&lt;script&gt;`にエスケープすることを実機で確認済み） |
| 5 | 認証 | DBの`password_hash`列を確認 | 問題なし（bcryptハッシュで保存されていることを確認済み） |
| 6 | 権限 | userBが他人の本にアクセス・編集・削除 | **不具合あり → 修正**（`findOwnBook`に`user_id`の一致確認を復元） |
| 7 | 通信 | 公開先URLがHTTPSか確認 | **点検できない（後述）** |
| 8 | エラー表示 | 20,000字の感想を送信 | **不具合あり → 修正**（エラーハンドリングミドルウェアを追加。詳細はサーバー側ログのみに出し、画面には「エラーが発生しました。」のみ表示） |
| 9 | 依存関係 | `npm outdated` / `npm audit` | 問題なし（0件、更新確認の手段はある） |
| 10 | ログ | ソース中の`console.*`呼び出しを確認 | 問題なし（パスワード・メールアドレスを出力する箇所なし） |

### 項目7（通信）が点検できない件について

項目7の点検プロンプトは「公開先のURLがHTTPSで始まっているか確認してください」であり、
これは**公開後でなければ実行できない**。Phase 7はPhase 8（リリースする）より前にあり、
この時点で公開先URLは存在しない。Phase 7の完了条件は「10項目すべてについて『問題なし』と
言える状態にする」だが、項目7だけは原理的にこの時点で満たせない。

Phase 8の本文（手順3「公開前の最終確認」）を確認したが、Phase 7で点検した「秘密情報」の
再確認のみで、通信（HTTPS）の確認には触れていない。Phase 8の完了条件にもHTTPSの項目はない。
**項目7を実際に確認する場所が本文のどこにもない。これは本文の欠落と判断した。**

### 修正後の回帰確認（Phase 6の再実施）

8機能すべてを、正常な値で再度一通り実行し、想定どおりのステータスコードが返ることを確認した。
エラーログなし。

---

## Phase 8 リリースする

実際の公開はせず、手順が実行可能かを確認した。

- **手順1・2（公開先の比較・決定）**：判断の手順であり、コードの実行を伴わない。本文どおり進められる
- **手順3（公開前の最終確認）**：`.env`が一度もコミットされていないこと、コード中に秘密情報の
  直書きがないことを確認した（上記Phase 7の項目1と同じ確認）。問題なし
- **手順4（戻せる状態）**：`git log`でコミットが4つ積まれており、`git revert`等で戻せる状態を確認した。
  データベース（SQLiteファイル）については、本文が「別途バックアップしておく」とだけ書いており、
  具体的な方法（ファイルをコピーする等）までは書かれていない。ReadLogの場合は単一ファイルなので
  実害は小さいと判断し、今回は指摘に留める
- **手順5（デプロイ）**：実際の公開は行わず、`NODE_ENV=production`を付けて起動確認をした

```
NODE_ENV=production PORT=4000 node src/app.js
```

**新たな警告を確認した：**

```
Warning: connect.session() MemoryStore is not
designed for a production environment, as it will leak
memory, and will not scale past a single process.
```

起動自体は成功し（`GET /login`は200）、機能は動く。しかしこれはexpress-session自身が出す警告で、
「セッションの保存先（デフォルトのMemoryStore）は本番運用に向かない」という指摘だ。
本文・shared/を検索したが、セッションの保存先についての記述は一つもない。
Phase 4はセッションという言葉自体は導入しているが、保存先の話はしていない。
**これも本文が触れていない箇所だが、起動自体は失敗しないため、詰まりとしては扱わず、
所見として記録するに留めた。**

- **手順6（公開後の動作確認）**：実際に公開していないため実施せず

### この段階で見つかった本文側の欠落（まとめ）

1. **Phase 6のReadLog実例が、極端な入力（感想欄に非常に長い文章）で見つかった不具合を書いていない**
   （異常系の権限バグとは扱いが非対称）
2. **項目7（通信・HTTPS）を実際に点検できる場所が本文のどこにもない**
   （Phase 7では公開前で確認不能、Phase 8では確認手順自体がない）
3. （軽微・所見）express-session の既定のセッション保存先（MemoryStore）が本番向けでない旨を
   本文のどこも説明していない。起動は失敗しないため、詰まりとしては扱っていない

Phase 6・7・8とも、実装を進められなくなるような「詰まり」（本文どおりにやったら先に進めなくなる箇所）
は発生しなかった。今回見つかったのは、いずれも「進めることはできるが、本文の説明が実際の挙動と
食い違っている・欠けている」という種類の欠落。

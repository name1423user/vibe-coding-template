# 進捗メモ（Claude Code 作業引き継ぎ用）

このファイルは読者向けではない。次にこのリポジトリで作業するセッション（自分自身）が、
迷わず・食い違えずに続きから着手できるようにするための引き継ぎメモ。
本文の一部ではないので、outline.md や CLAUDE.md の執筆規律の対象外。

最終更新：2026-09-10

## まず確認すること

```
git branch -a
git log --oneline -5
```

**作業ブランチは `claude/manuscript-chapter-writing-pii5y5`。** これ以外のブランチ
（特に空に近いブランチ）にいたら、それは取り違え。過去に一度、別セッションが
インポート直後の空ブランチ（`claude/manuscript-consistency-check-3b7m7e`、既にリモートで削除済み）
で作業しようとして「原稿が全部空に見える」という誤報告をしたことがある。
このリポジトリのリモートの `HEAD`（デフォルトブランチ）は `claude/new-session-dqpcvx` で、
これはインポート直後の空状態のまま。実作業は全部 `claude/manuscript-chapter-writing-pii5y5` にある。

不安になったら `git log origin/claude/manuscript-chapter-writing-pii5y5 --oneline` で
リモート側の最新コミットを確認する。

## 進捗状況（2026-09-10時点）

### 完了

- 通し課題確定：読書記録アプリ「ReadLog」（`shared/running-example.md`）
- 第0部・第1部・第3部・第4部・第5部・第6部：執筆済み
- 第2部 Phase 0〜8：全章執筆済み
- 付録A・B：`scripts/build_appendix.py` で自動生成
- 付録C：トラブルシューティング早見表。各Phaseの「よくある失敗と戻り先」から**自動生成**するよう
  `scripts/build_appendix.py` を拡張済み（症状の見出しと「Phase Nの手順M」の正規表現抽出）
- 付録E：通し課題の完成コード。**実際にコードを書いて動かして検証済み**（詳細は次項）
- 付録F：次に学ぶこと（6項目）

### 未着手

- **付録D 環境構築の詰まり対処**（OS別・よくあるエラー別）。次にやるべき作業はこれ。
  下記「付録Dの執筆に使える素材」を参照すること。

## 直近のセッションでやったこと（実機ビルド検証）

ユーザーから「本文からコードを組み立てるのではなく、実際にReadLogを作って動かせ」と指示され、
`scratchpad/readlog/` に実際にNode.jsプロジェクトを作り、Phase 4〜8の手順を**本文に書かれた通りに**
1行ずつ実行した。詳細ログは `.claude/notes/readlog-build-log.md` に保存済み（scratchpadは
セッション終了で消えるため、ここに複製してある）。

**重要：scratchpadの実行環境自体は次のセッションには残っていない。** ただし再現条件は
記録してある（Node v22.22.2 / npm 10.9.7、`npm install express better-sqlite3 express-session
bcrypt ejs dotenv` で同じバージョンが入るはず）。付録Eのコードをそのまま `readlog/` に展開して
`npm install && node src/app.js` すれば同じ状態を再現できる。

この検証で、本文の欠落を4件見つけ、うち3件をユーザーの指示のもとで本文修正済み：

1. **Phase 4にdotenvの読み込み手順が欠けていた**（`secret option required for sessions`で
   全機能が止まる）→ 修正済み（dotenvを手順2に追加、手順4に読み込み方法と理由を追加、
   よくある失敗に1項目追加）
2. **Phase 6が極端な入力（20,000字）で見つかった不具合（413＋生のスタックトレース露出）を
   報告していなかった** → 修正済み（Phase 6の実例に追記、Phase 7・第4部4-8に接続、
   よくある失敗に1項目追加）
3. **Phase 7の項目7（通信・HTTPS）が、公開前のPhase 7では原理的に点検不可能だった**
   （完了条件が「10項目すべて」なのに、公開先URLがまだ存在しない）→ 修正済み
   （Phase 7は項目7をPhase 8に明示的に持ち越す設計に変更。`shared/phases.md`も同期済み）
4. **express-sessionの既定のセッション保存先（MemoryStore）が本番運用に向かない警告が出る件**
   → ユーザー判断で「本文には書かない、範囲外」。付録Fに1項目だけ追加して対応済み

権限バグ（他人の本のURLに直接アクセスすると見えてしまう）も実際に再現し、
「Phase 6で見つかりPhase 7で直す」という本文の筋書きが技術的に正確であることを確認済み。

## 付録Dの執筆に使える素材

`.claude/notes/readlog-build-log.md` に、コマンドとエラー全文を含めて記録してある。
特に付録Dの「よくあるエラー別」の候補になりそうなもの：

- `npm install <パッケージ名>` を `package.json` がないフォルダで実行したときの挙動
  （npm 10系は自動生成するので詰まりにはならないが、素っ気ない`package.json`になる）
- `secret option required for sessions`（dotenv未導入 or 読み込み忘れ）
- `PayloadTooLargeError: request entity too large`（body-parserの既定上限、413）
- `Warning: connect.session() MemoryStore is not designed for a production environment`
  （`NODE_ENV=production`で起動したときだけ出る）

OS別の詰まり（Windows/Mac/Linuxの違い、better-sqlite3やbcryptのネイティブビルド失敗など）は
今回の検証環境（Linuxコンテナ、prebuildが効いた）では再現していない。ここは実機で踏んでいないので、
本文の他の部分と同じ「実際に踏んだものだけを書く」規律を守るなら、AIの一般知識で埋めるのではなく、
確認できる範囲に絞るか、その旨を明記する必要がある。着手前にユーザーに方針を確認すること。

## 次にやるとしたら

1. `.claude/notes/readlog-build-log.md` を読み直す
2. 付録Dの構成をユーザーと相談する（OS別に実機で踏めない部分をどう扱うか）
3. 書いたら `python scripts/check.py` → 指摘0件を確認
4. 付録Dは自動生成の対象外（手書き）なので `build_appendix.py` の実行は不要
5. コミット・プッシュ

## PR

このリポジトリはPRテンプレートを持たない（`find . -iname "*pull_request_template*"` で確認済み）。
デフォルトブランチは `claude/new-session-dqpcvx`（空のインポート状態）なので、PRのベースは
明示的にそこを指定する。

# 国債 投資家別売買動向ダッシュボード

日本証券業協会「公社債店頭売買高」の「(Ｋ)一般差引」シートから、国債の投資家別・年限別の売買動向を表示するサイトです。
GitHub Pages で公開し、GitHub Actions が毎日 JSDA のサイトを確認して、新しい月や訂正が出ると自動で更新します。

## ファイル構成

| ファイル | 役割 |
|---|---|
| `index.html` | 公開されるサイト本体（自動生成） |
| `template.html` | サイトのひな形（デザインや機能を変えるときはここを編集） |
| `data/raw.json` | 取り込み済みのデータ（元データの符号：売付額−買付額） |
| `scripts/update.py` | JSDA からファイルを取得して `index.html` を作り直すプログラム |
| `.github/workflows/update.yml` | 毎日 18:30（日本時間）に `update.py` を実行する設定 |

## 初回の設定（会社のパソコン以外で、ブラウザだけで完了します）

1. **GitHub アカウントを作る**：https://github.com で無料登録します。
2. **リポジトリを作る**：右上の「＋」→「New repository」。名前は例えば `jgb-flows`、公開範囲は **Public** を選び、「Create repository」。
   （無料プランの GitHub Pages は Public リポジトリが対象です。元データは公表統計です。）
3. **ファイルをアップロード**：「uploading an existing file」をクリックし、zip を展開した中の `index.html`、`template.html`、`README.md`、`data` フォルダ、`scripts` フォルダをドラッグして「Commit changes」。
4. **自動更新の設定ファイルを作る**：「Add file」→「Create new file」。ファイル名の欄に `.github/workflows/update.yml` と入力し、同梱の `update.yml` の中身を貼り付けて「Commit changes」。
   （`.github` はドットで始まるフォルダのため、ドラッグでは上がらないことがあります。この方法が確実です。）
5. **書き込み権限を許可**：「Settings」→「Actions」→「General」→「Workflow permissions」で **Read and write permissions** を選んで「Save」。
6. **サイトを公開**：「Settings」→「Pages」→「Build and deployment」の Source を **Deploy from a branch**、Branch を **main / (root)** にして「Save」。
   数分後、`https://<ユーザー名>.github.io/jgb-flows/` でサイトが開けます。
7. **動作確認**：「Actions」タブ →「JSDAデータの自動更新」→「Run workflow」。緑のチェックが付けば成功です（変更がなければ「変更なし」で終わります）。

## 日々の運用

- 何もしなくても、毎日 18:30 に JSDA のページを確認し、新しい月（毎月20日ごろ公表）や過去データの訂正があれば自動で反映します。
- すぐに反映したいときは「Actions」→「Run workflow」で手動実行できます。
- 年度が替わって新しい年度別ファイル（例：`koushasai2026.xlsx`）が掲載されても、ページ上のリンクを自動で見つけて取り込みます。

## うまくいかないとき

- **Actions が赤い×で失敗する**：失敗した実行を開くとログが見られます。「リンクが見つかりませんでした」と出る場合は JSDA のページ構成が変わった可能性があるので、`scripts/update.py` の `INDEX_URL` や取り出し方を見直します。
- **push で権限エラーが出る**：手順5の設定を確認してください。
- **自動実行が止まった**：GitHub は、リポジトリに60日間動きがないと定期実行を止めることがあります。「Actions」タブに表示される案内から再開できます（通常は毎月のデータ更新で動きがあるため止まりません）。
- **会社のパソコンで開けない**：社内ネットワークで `github.io` への接続が制限されている可能性があります。情報システム部門に確認してください。

## 手元で試す場合（任意）

```bash
pip install pandas openpyxl
python scripts/update.py --local ダウンロードしたxlsxのフォルダ --force
```

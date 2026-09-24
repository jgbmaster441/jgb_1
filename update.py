"""
日本証券業協会「公社債店頭売買高」から国債の投資家別データを取り込み、index.html を作り直すスクリプト。

  python scripts/update.py             # JSDAのサイトから最新ファイルを取得して更新
  python scripts/update.py --local DIR # DIR内の koushasai*.xlsx から更新（手元のファイルで試すとき）

データは data/raw.json に保存します（元データの符号：売付額−買付額）。
"""
import argparse, datetime, glob, io, json, os, re, sys, time, urllib.request
from urllib.parse import urljoin
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_URL = "https://www.jsda.or.jp/shiryoshitsu/toukei/tentoubaibai/index.html"
RAW_PATH = os.path.join(ROOT, "data", "raw.json")
TPL_PATH = os.path.join(ROOT, "template.html")
OUT_PATH = os.path.join(ROOT, "index.html")
UA = {"User-Agent": "Mozilla/5.0 (compatible; jgb-flows-dashboard/1.0)"}
EN = ['City Banks & Long-Term Credit Banks','Regional Banks','Trust Banks','Fin.Insts. for Agr. & Forestry',
      '2nd Regional','Shinkin Banks','Other Fin.Insts.','Life & Non-Life Insurance Companies','Investment Trusts',
      'Mutual Aid Association of Govt.Offices','Business Corporations','Other Corporations','Foreigners',
      'Individuals','Others','Bond Dealers','Total']
# (Ｋ)一般差引 シートの D〜I 列：国債計, 超長期, 利付長期, 利付中期, 割引, 国庫短期証券等
COLS = range(3, 9)


def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(5 * (i + 1))


def list_remote_files():
    html = fetch(INDEX_URL).decode("utf-8", errors="replace")
    links = sorted(set(re.findall(r'href="([^"]*koushasai[^"]*\.xlsx)"', html)))
    urls = [urljoin(INDEX_URL, l) for l in links]
    if not urls:
        sys.exit("JSDAのページからExcelファイルのリンクが見つかりませんでした。ページの構成が変わった可能性があります。")
    return urls


def parse_book(data, name):
    xl = pd.ExcelFile(io.BytesIO(data))
    sheets = [s for s in xl.sheet_names if "一般差引" in s and "証券" not in s]
    if not sheets:
        print(f"  スキップ：{name}（「(Ｋ)一般差引」シートなし）")
        return {}
    df = xl.parse(sheets[0], header=None)
    out = {}
    for _, r in df.iterrows():
        m, en = str(r[0]).strip(), str(r[2]).strip()
        if not re.fullmatch(r"\d{4}/\d{2}", m) or en not in EN:
            continue
        try:
            vals = [int(round(float(r[c]))) for c in COLS]
        except (TypeError, ValueError):
            continue
        out.setdefault(m, {})[en] = vals
    good = {m: v for m, v in out.items() if len(v) == len(EN)}
    bad = sorted(set(out) - set(good))
    if bad:
        print(f"  注意：{name} の {', '.join(bad)} は投資家区分がそろっていないため取り込みません")
    print(f"  {name}: {min(good) if good else '-'}〜{max(good) if good else '-'}（{len(good)}か月）")
    return good


def load_raw():
    if not os.path.exists(RAW_PATH):
        return {}
    raw = json.load(open(RAW_PATH, encoding="utf-8"))
    return {m: {e: raw["d"][e][k] for e in EN} for k, m in enumerate(raw["m"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", help="koushasai*.xlsx を置いたフォルダ")
    ap.add_argument("--force", action="store_true", help="変更がなくてもindex.htmlを作り直す")
    args = ap.parse_args()

    months = load_raw()
    before = json.dumps(months, sort_keys=True)

    if args.local:
        files = [(p, open(p, "rb").read()) for p in sorted(glob.glob(os.path.join(args.local, "koushasai*.xlsx")))]
    else:
        files = []
        for u in list_remote_files():
            print("取得:", u)
            files.append((u, fetch(u + "?t=" + str(int(time.time())))))  # キャッシュ回避
    # 年度別ファイル → 最新年度ファイル（koushasai.xlsx）の順に上書き
    files.sort(key=lambda f: (os.path.basename(f[0]) == "koushasai.xlsx", f[0]))
    for name, data in files:
        months.update(parse_book(data, os.path.basename(name)))

    changed = before != json.dumps(months, sort_keys=True)
    if not changed and not args.force and os.path.exists(OUT_PATH):
        print("変更なし。")
        return

    ms = sorted(months)
    jst = datetime.timezone(datetime.timedelta(hours=9))
    raw = {"m": ms, "d": {e: [months[m][e] for m in ms] for e in EN},
           "updated": datetime.datetime.now(jst).strftime("%Y-%m-%d %H:%M JST")}
    os.makedirs(os.path.dirname(RAW_PATH), exist_ok=True)
    json.dump(raw, open(RAW_PATH, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

    tpl = open(TPL_PATH, encoding="utf-8").read()
    enc = json.dumps(raw, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    open(OUT_PATH, "w", encoding="utf-8").write(tpl.replace("__DATA_SLOT__", enc))
    print(f"更新しました：{ms[0]}〜{ms[-1]}（{len(ms)}か月）")


if __name__ == "__main__":
    main()

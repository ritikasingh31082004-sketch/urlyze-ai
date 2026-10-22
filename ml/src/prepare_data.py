"""
Clean the raw dataset and extract features.

Output labels: 1 = phishing, 0 = legitimate.

Usage:
  python ml/src/prepare_data.py --input ml/data/raw/PhiUSIIL_Phishing_URL_Dataset.csv --legit-label 1
  python ml/src/prepare_data.py --input ml/data/raw/phishing_site_urls.csv --legit-label good
"""
import argparse
from pathlib import Path

import pandas as pd

from features import extract_features, get_host, strip_artifacts

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, nargs="+", help="one or more CSV files")
    ap.add_argument("--legit-label", required=True, nargs="+",
                    help="legit label value for each CSV, same order (e.g. 1 good)")
    ap.add_argument("--sample", type=int, default=0, help="optional: use N rows (quick tests)")
    a = ap.parse_args()

    if len(a.input) != len(a.legit_label):
        raise SystemExit("Give one --legit-label value per --input file")
    frames = []
    for path_, legit_ in zip(a.input, a.legit_label):
        d = pd.read_csv(path_)
        cols = {c.lower(): c for c in d.columns}
        uc, lc = cols.get("url"), cols.get("label")
        if not uc or not lc:
            raise SystemExit(f"Need 'URL' and 'label' columns in {path_}, found: {list(d.columns)}")
        d = d[[uc, lc]].rename(columns={uc: "url", lc: "label"})
        d["label"] = (d["label"].astype(str).str.lower() != str(legit_).lower()).astype(int)  # 1 = phishing
        d["source"] = Path(path_).stem
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)

    print("Raw rows:", len(df))
    df = df.dropna()
    df["url"] = df["url"].astype(str).str.strip()
    df = df[df["url"].str.len() > 3]
    df["_key"] = df["url"].map(strip_artifacts).str.lower()
    df = df.drop_duplicates(subset="_key").drop(columns="_key")
    if a.sample:
        df = df.sample(min(a.sample, len(df)), random_state=42)
    print("After cleaning:", len(df))
    print(df.groupby(["source", "label"]).size())

    feats = pd.DataFrame([extract_features(u) for u in df["url"]])
    out = pd.concat([df.reset_index(drop=True), feats], axis=1)
    out["host"] = [get_host(u) for u in out["url"]]  # used for leak-free splitting
    path = ROOT / "data" / "processed" / "features.csv"
    out.to_csv(path, index=False)
    print("Saved ->", path, out.shape)


if __name__ == "__main__":
    main()

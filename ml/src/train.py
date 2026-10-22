"""
Train + compare multiple models, pick the best, save artifacts.

The split is grouped by hostname so the same domain never appears in both
train and test (prevents inflated, leaky accuracy).
"""
import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, f1_score,
                             precision_score, recall_score, roc_auc_score, roc_curve)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from features import FEATURE_NAMES

# Remove dataset-shortcut features so the model must learn real patterns
DROP = {"is_https", "has_www"}
FEATURES = [f for f in FEATURE_NAMES if f not in DROP]

try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None

ROOT = Path(__file__).resolve().parents[1]
REPORTS, MODELS = ROOT / "reports", ROOT / "models"
REPORTS.mkdir(exist_ok=True)
MODELS.mkdir(exist_ok=True)


def main():
    df = pd.read_csv(ROOT / "data" / "processed" / "features.csv")
    X, y = df[FEATURES].values, df["label"].values
    groups = df["host"].fillna("").values

    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    tr, te = next(gss.split(X, y, groups))
    Xtr, Xte, ytr, yte = X[tr], X[te], y[tr], y[te]
    print(f"Train {len(tr)} | Test {len(te)} | phishing share (test): {yte.mean():.2%}")

    models = {
        "Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced")),
        "Decision Tree": DecisionTreeClassifier(max_depth=12, class_weight="balanced", random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=200, n_jobs=-1, class_weight="balanced", random_state=42),
        "Gradient Boosting": GradientBoostingClassifier(random_state=42),
    }
    if XGBClassifier:
        models["XGBoost"] = XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1,
                                          eval_metric="logloss", n_jobs=-1, random_state=42)

    rows, fitted, probas = [], {}, {}
    for name, m in models.items():
        print("Training", name, "...")
        m.fit(Xtr, ytr)
        pred, proba = m.predict(Xte), m.predict_proba(Xte)[:, 1]
        fitted[name], probas[name] = m, proba
        rows.append({"model": name,
                     "accuracy": accuracy_score(yte, pred),
                     "precision": precision_score(yte, pred),
                     "recall": recall_score(yte, pred),
                     "f1": f1_score(yte, pred),
                     "roc_auc": roc_auc_score(yte, proba)})

    res = pd.DataFrame(rows).sort_values("f1", ascending=False).reset_index(drop=True)
    res.round(4).to_csv(REPORTS / "model_comparison.csv", index=False)
    print("\n", res.round(4).to_string(index=False))

    best_name = res.loc[0, "model"]
    best = fitted[best_name]
    print("\nBest model:", best_name)

    # accuracy per data source on the test set
    te_df = df.iloc[te].copy()
    te_df["pred"] = best.predict(Xte)
    print("\nAccuracy by source / class (test set):")
    print(te_df.assign(ok=(te_df["pred"] == te_df["label"]))
               .groupby(["source", "label"])["ok"].agg(["mean", "size"]).round(4))

    # ---- charts ----
    ax = res.set_index("model")[["accuracy", "precision", "recall", "f1"]].plot.bar(figsize=(10, 5), ylim=(0.5, 1.0))
    ax.set_title("Model comparison")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(REPORTS / "model_comparison.png", dpi=150)
    plt.close()

    ConfusionMatrixDisplay.from_predictions(yte, best.predict(Xte),
                                            display_labels=["Legitimate", "Phishing"], cmap="Blues")
    plt.title(f"Confusion matrix - {best_name}")
    plt.tight_layout()
    plt.savefig(REPORTS / "confusion_matrix.png", dpi=150)
    plt.close()

    plt.figure(figsize=(6, 5))
    for name, p in probas.items():
        fpr, tpr, _ = roc_curve(yte, p)
        plt.plot(fpr, tpr, label=name)
    plt.plot([0, 1], [0, 1], "k--")
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("ROC curves")
    plt.legend()
    plt.tight_layout()
    plt.savefig(REPORTS / "roc_curves.png", dpi=150)
    plt.close()

    # feature importance (feeds the explainability panel later)
    est = best[-1] if hasattr(best, "steps") else best
    imp = getattr(est, "feature_importances_", None)
    if imp is None and hasattr(est, "coef_"):
        imp = np.abs(est.coef_[0])
    if imp is not None:
        s = pd.Series(imp, index=FEATURES).sort_values(ascending=False)
        s.head(15)[::-1].plot.barh(figsize=(7, 6), title=f"Top features - {best_name}")
        plt.tight_layout()
        plt.savefig(REPORTS / "feature_importance.png", dpi=150)
        plt.close()
        s.to_csv(REPORTS / "feature_importance.csv")

    # ---- save artifacts ----
    joblib.dump({"model": best, "features": FEATURES, "name": best_name}, MODELS / "urlyze_model.joblib")
    with open(MODELS / "metadata.json", "w") as f:
        json.dump({"best_model": best_name, "metrics": res.drop(columns="model").iloc[0].round(4).to_dict(),
                   "train_size": int(len(tr)), "test_size": int(len(te))}, f, indent=2)
    print("Saved model ->", MODELS / "urlyze_model.joblib")


if __name__ == "__main__":
    main()

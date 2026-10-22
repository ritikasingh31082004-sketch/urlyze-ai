"""
URLYZE AI - analysis engine.
Loads the trained model, scores a URL, and builds human-readable risk factors.
"""
import csv
import json
import re
import sys
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml" / "src"))
from features import (RISKY_TLDS, SECOND_LEVEL, extract_features,  # noqa: E402
                      get_host, strip_artifacts)

MODEL_PATH = ROOT / "ml" / "models" / "urlyze_model.joblib"
META_PATH = ROOT / "ml" / "models" / "metadata.json"
COMPARE_PATH = ROOT / "ml" / "reports" / "model_comparison.csv"

_bundle = joblib.load(MODEL_PATH)
MODEL, FEATURES, MODEL_NAME = _bundle["model"], _bundle["features"], _bundle["name"]

# Well-known domains: URL-only models can false-alarm on these (e.g. /signin pages).
TRUSTED_DOMAINS = {
    "google.com", "youtube.com", "gmail.com", "microsoft.com", "live.com",
    "office.com", "apple.com", "icloud.com", "amazon.com", "amazon.in",
    "facebook.com", "instagram.com", "whatsapp.com", "twitter.com", "x.com",
    "linkedin.com", "github.com", "gitlab.com", "wikipedia.org", "paypal.com",
    "netflix.com", "dropbox.com", "adobe.com", "zoom.us", "stackoverflow.com",
    "flipkart.com", "sbi.co.in", "hdfcbank.com", "icicibank.com", "irctc.co.in",
    "gov.in", "nic.in", "python.org", "mozilla.org", "openai.com", "anthropic.com",
}

# brand keyword -> legitimate registered domains
BRANDS = {
    "paypal": {"paypal.com"}, "google": {"google.com"}, "microsoft": {"microsoft.com", "live.com"},
    "apple": {"apple.com", "icloud.com"}, "amazon": {"amazon.com", "amazon.in"},
    "facebook": {"facebook.com"}, "instagram": {"instagram.com"}, "netflix": {"netflix.com"},
    "whatsapp": {"whatsapp.com"}, "sbi": {"sbi.co.in"}, "hdfc": {"hdfcbank.com"},
    "icici": {"icici.com", "icicibank.com"}, "paytm": {"paytm.com"}, "flipkart": {"flipkart.com"},
}

SUSPICIOUS_WORDS = ["login", "signin", "verify", "update", "secure", "account", "bank",
                    "confirm", "password", "wallet", "billing", "suspend", "unlock", "recover"]


def registered_domain(host: str) -> str:
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    if len(parts[-1]) == 2 and parts[-2] in SECOND_LEVEL and len(parts) >= 3:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def is_trusted(host: str) -> bool:
    return any(host == d or host.endswith("." + d) for d in TRUSTED_DOMAINS)


def level_for(score: int) -> str:
    return "LOW" if score < 35 else "MEDIUM" if score < 65 else "HIGH"


def build_factors(url: str, f: dict, host: str, trusted: bool) -> list:
    out = []

    def add(kind, title, detail):
        out.append({"type": kind, "title": title, "detail": detail})

    low = url.lower()
    if f["has_ip_host"]:
        add("danger", "IP address used as host", "Legitimate sites almost always use a domain name.")
    if f["has_at"]:
        add("danger", "Contains '@' symbol", "Browsers ignore text before '@', which can hide the real destination.")
    if f["has_punycode"]:
        add("danger", "Punycode (xn--) domain", "May be a look-alike domain using foreign characters.")
    if f["is_shortener"]:
        add("warning", "URL shortener", "The real destination is hidden behind a short link.")
    if f["risky_tld"]:
        add("warning", "High-risk domain ending", "This domain ending is frequently used in abusive sites.")
    words = [w for w in SUSPICIOUS_WORDS if w in low]
    if words and not trusted:
        add("warning", "Suspicious keywords", "Found: " + ", ".join(words[:5]) + ".")
    if f["num_subdomains"] >= 3:
        add("warning", "Many subdomains", f"{f['num_subdomains']} subdomain levels can hide the real domain.")
    if f["host_hyphen_count"] >= 2:
        add("warning", "Many hyphens in domain", "Long hyphenated names are common in fake sites.")
    if f["url_length"] > 75:
        add("warning", "Very long URL", f"{f['url_length']} characters; long URLs can hide malicious parts.")
    if f["has_port"]:
        add("warning", "Unusual port number", "Normal sites rarely specify a port.")
    if f["double_slash_in_path"]:
        add("warning", "Double slash in path", "Can indicate a redirect trick.")

    reg = registered_domain(host)
    for brand, real in BRANDS.items():
        if brand in host and reg not in real:
            add("danger", f"Possible '{brand}' impersonation",
                f"Domain contains '{brand}' but belongs to '{reg}', not the real brand.")
            break

    if trusted:
        add("safe", "Recognized trusted domain", f"{registered_domain(host)} is on the trusted list.")
    if url.lower().startswith("https://"):
        add("safe", "HTTPS enabled", "Encrypted connection (note: phishing sites can use HTTPS too).")
    elif url.lower().startswith("http://"):  # no scheme typed = unknown, so no claim
        add("warning", "No HTTPS", "The connection is not encrypted.")
    if not any(x["type"] in ("danger", "warning") for x in out):
        add("safe", "No suspicious patterns found", "The URL structure looks normal.")
    return out


def analyze(url: str) -> dict:
    url = url.strip()
    f = extract_features(url)
    host = get_host(url)
    proba = float(MODEL.predict_proba([[f[n] for n in FEATURES]])[0][1])

    trusted = bool(host) and is_trusted(host)
    final = min(proba, 0.05) if trusted else proba
    score = round(final * 100)
    level = level_for(score)
    verdict = {"LOW": "Looks safe", "MEDIUM": "Be careful", "HIGH": "Likely phishing"}[level]

    return {
        "url": url,
        "host": host,
        "risk_score": score,
        "level": level,
        "verdict": verdict,
        "model_probability": round(proba * 100, 1),
        "trusted_domain": trusted,
        "factors": build_factors(url, f, host, trusted),
        "features": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in f.items()},
        "model": MODEL_NAME,
    }


def model_info() -> dict:
    meta = json.loads(META_PATH.read_text()) if META_PATH.exists() else {}
    rows = []
    if COMPARE_PATH.exists():
        with open(COMPARE_PATH, newline="") as fh:
            rows = list(csv.DictReader(fh))
    return {"metadata": meta, "comparison": rows}

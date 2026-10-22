"""
URLYZE AI - lexical URL feature extraction.

Pure string analysis (no network calls), so training and the FastAPI
backend use the exact same code and results are fast + reproducible.
"""
import math
import re
from collections import Counter
from urllib.parse import urlparse

SUSPICIOUS_WORDS = [
    "login", "signin", "verify", "update", "secure", "account", "bank",
    "confirm", "password", "paypal", "wallet", "free", "bonus", "gift",
    "billing", "support", "suspend", "unlock", "recover", "invoice",
]
SHORTENERS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd",
    "buff.ly", "rebrand.ly", "cutt.ly", "shorturl.at",
}
RISKY_TLDS = {
    "xyz", "top", "tk", "ml", "ga", "cf", "gq", "click", "link", "work",
    "support", "zip", "country", "kim", "loan", "men", "icu", "buzz",
}
SECOND_LEVEL = {"co", "com", "org", "net", "gov", "ac", "edu"}
IP_RE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")

FEATURE_NAMES = [
    "url_length", "host_length", "path_length", "query_length",
    "num_dots", "num_hyphens", "num_underscores", "num_slashes",
    "num_digits", "digit_ratio", "letter_ratio", "num_special_chars",
    "has_at", "num_question", "num_equals", "num_ampersand", "num_percent",
    "has_ip_host", "is_https", "num_subdomains", "tld_length", "risky_tld",
    "suspicious_word_count", "is_shortener", "url_entropy", "host_entropy",
    "has_punycode", "has_port", "double_slash_in_path", "longest_token_len",
    "host_digit_count", "host_hyphen_count", "path_depth", "has_www",
]


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum(c / n * math.log2(c / n) for c in counts.values())


def normalize(url: str) -> str:
    url = url.strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "http://" + url
    return url


def strip_artifacts(url: str) -> str:
    """Remove scheme and leading 'www.' so datasets' formatting quirks
    (e.g. legitimate URLs always written as https://www.) can't be learned."""
    u = url.strip()
    u = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", "", u)
    u = re.sub(r"^www\.", "", u, flags=re.IGNORECASE)
    return u


def get_host(url: str) -> str:
    try:
        return (urlparse(normalize(url)).hostname or "").lower()
    except ValueError:
        return ""


def extract_features(url: str) -> dict:
    original = url.strip()
    raw = strip_artifacts(original)          # features come from the cleaned URL
    full = "http://" + raw
    try:
        p = urlparse(full)
        host = (p.hostname or "").lower()
        port = p.port
    except ValueError:
        p, host, port = urlparse("http://invalid"), "", None
    path, query = p.path or "", p.query or ""
    low = raw.lower()

    parts = host.split(".") if host else []
    is_ip = bool(IP_RE.match(host))
    tld = parts[-1] if len(parts) > 1 and not is_ip else ""
    base_len = 3 if len(parts) >= 3 and parts[-2] in SECOND_LEVEL and len(tld) == 2 else 2
    num_sub = 0 if is_ip else max(len(parts) - base_len, 0)
    letters = sum(c.isalpha() for c in raw)
    digits = sum(c.isdigit() for c in raw)
    n = max(len(raw), 1)
    tokens = re.split(r"[^a-zA-Z0-9]+", raw)

    return {
        "url_length": len(raw),
        "host_length": len(host),
        "path_length": len(path),
        "query_length": len(query),
        "num_dots": raw.count("."),
        "num_hyphens": raw.count("-"),
        "num_underscores": raw.count("_"),
        "num_slashes": raw.count("/"),
        "num_digits": digits,
        "digit_ratio": digits / n,
        "letter_ratio": letters / n,
        "num_special_chars": sum(not c.isalnum() for c in raw),
        "has_at": int("@" in raw),
        "num_question": raw.count("?"),
        "num_equals": raw.count("="),
        "num_ampersand": raw.count("&"),
        "num_percent": raw.count("%"),
        "has_ip_host": int(is_ip),
        "is_https": int(original.lower().startswith("https://")),
        "num_subdomains": num_sub,
        "tld_length": len(tld),
        "risky_tld": int(tld in RISKY_TLDS),
        "suspicious_word_count": sum(w in low for w in SUSPICIOUS_WORDS),
        "is_shortener": int(host in SHORTENERS),
        "url_entropy": _entropy(raw),
        "host_entropy": _entropy(host),
        "has_punycode": int("xn--" in host),
        "has_port": int(port is not None),
        "double_slash_in_path": int("//" in path),
        "longest_token_len": max((len(t) for t in tokens), default=0),
        "host_digit_count": sum(c.isdigit() for c in host),
        "host_hyphen_count": host.count("-"),
        "path_depth": len([s for s in path.split("/") if s]),
        "has_www": int(re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", "", original.lower()).startswith("www.")),
    }


def features_vector(url: str) -> list:
    f = extract_features(url)
    return [f[name] for name in FEATURE_NAMES]

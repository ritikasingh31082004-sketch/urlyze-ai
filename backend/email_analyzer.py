"""
URLYZE AI - email phishing analysis.

Hybrid approach:
  1. Text analysis: urgency, credential requests, prize lures, threats, generic greetings,
     attachment tricks, shouting (rule-based, fully explainable).
  2. Sender analysis: brand name in the display name that doesn't match the sender's domain.
  3. Link analysis: every link is scored by the trained URL model (analyzer.analyze).
"""
import re

from analyzer import BRANDS, analyze as analyze_url, level_for, registered_domain

URGENCY = ["urgent", "urgently", "immediately", "act now", "right away", "within 24 hours",
           "within 48 hours", "final notice", "final warning", "last warning", "last chance",
           "expires today", "expire soon", "limited time", "as soon as possible", "deadline",
           "action required", "immediate action", "response required"]
CREDENTIALS = ["verify your account", "verify your identity", "confirm your identity",
               "confirm your password", "enter your password", "your password",
               "login credentials", "log in to your account", "sign in to your account",
               "update your payment", "update your billing", "payment details", "card number",
               "credit card", "debit card", "cvv", "pin number", "otp", "one time password",
               "social security", "ssn", "bank account", "account number", "aadhaar",
               "pan card", "net banking", "verify your email", "confirm your account"]
LURES = ["you have won", "you've won", "lottery", "prize", "claim your", "gift card",
         "inheritance", "refund", "wire transfer", "bitcoin", "crypto", "free gift",
         "congratulations", "selected as a winner", "cash reward", "unclaimed", "beneficiary",
         "million dollars"]
THREATS = ["account will be suspended", "account will be closed", "account has been suspended",
           "account has been locked", "account is locked", "temporarily suspended",
           "legal action", "terminate", "unauthorized", "unauthorised", "suspicious activity",
           "unusual activity", "security alert", "security breach", "compromised", "deactivated",
           "will be deleted", "penalty"]
GREETINGS = ["dear customer", "dear user", "dear member", "dear account holder",
             "dear valued customer", "dear client", "dear sir", "dear madam", "dear sir/madam",
             "dear email user", "dear friend"]
ATTACH_PHRASES = ["see attached", "attached file", "open the attachment", "download the attachment",
                  "enable macros", "enable content", "invoice attached", "attached document"]
ATTACH_EXT = re.compile(r"\.(exe|scr|zip|rar|js|vbs|iso|bat|docm|xlsm)\b", re.I)

FREE_PROVIDERS = {"gmail.com", "yahoo.com", "yahoo.in", "outlook.com", "hotmail.com", "aol.com",
                  "proton.me", "protonmail.com", "rediffmail.com"}
ORG_WORDS = ["bank", "support", "security", "service", "team", "billing", "helpdesk", "admin",
             "accounts", "official", "customer care"]

URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"'\)\]]+", re.I)
FROM_RE = re.compile(r"^\s*from\s*:\s*(.+)$", re.I | re.M)
SUBJECT_RE = re.compile(r"^\s*subject\s*:\s*(.+)$", re.I | re.M)
ADDR_RE = re.compile(r"^(.*?)<\s*([^>\s]+@[^>\s]+)\s*>\s*$")


def _find(phrases, text):
    found = []
    for p in phrases:
        if re.search(r"(?<!\w)" + re.escape(p) + r"(?!\w)", text):
            found.append(p)
    return found


def _parse_sender(raw):
    raw = raw.strip().strip('"')
    m = ADDR_RE.match(raw)
    if m:
        return m.group(1).strip().strip('"'), m.group(2).strip().lower()
    if "@" in raw:
        return "", raw.lower()
    return raw, ""


def analyze_email(text: str) -> dict:
    low = text.lower()
    factors, points = [], 0

    def add(kind, title, detail, pts=0):
        nonlocal points
        factors.append({"type": kind, "title": title, "detail": detail})
        points += pts

    subject_m, from_m = SUBJECT_RE.search(text), FROM_RE.search(text)
    subject = subject_m.group(1).strip() if subject_m else ""
    display, sender_addr = _parse_sender(from_m.group(1)) if from_m else ("", "")

    # --- text signals ---
    hit = _find(URGENCY, low)
    if hit:
        add("warning", "Urgent or pressuring language", "Found: " + ", ".join(hit[:4]) + ".", min(20, 7 * len(hit)))
    hit = _find(CREDENTIALS, low)
    if hit:
        add("danger", "Asks for sensitive information", "Found: " + ", ".join(hit[:4]) + ". Real companies rarely ask for this by email.", min(25, 12 * len(hit)))
    hit = _find(LURES, low)
    if hit:
        add("warning", "Prize, refund or money lure", "Found: " + ", ".join(hit[:4]) + ".", min(18, 9 * len(hit)))
    hit = _find(THREATS, low)
    if hit:
        add("warning", "Threat or scare tactic", "Found: " + ", ".join(hit[:4]) + ".", min(15, 7 * len(hit)))
    hit = _find(GREETINGS, low)
    if hit:
        add("warning", "Generic greeting", f"'{hit[0]}' - real senders usually use your name.", 8)
    if _find(ATTACH_PHRASES, low) or ATTACH_EXT.search(low):
        add("warning", "Pushes you to open an attachment", "Phishing emails often hide malware in attachments.", 12)

    words = re.findall(r"[A-Za-z]{3,}", text)
    caps = sum(1 for w in words if w.isupper())
    if (len(words) >= 10 and caps / len(words) > 0.3) or "!!" in text:
        add("warning", "Shouting or excessive punctuation", "Lots of CAPITAL LETTERS or '!!' to create panic.", 6)

    # --- sender ---
    if sender_addr:
        sender_domain = registered_domain(sender_addr.split("@")[-1])
        shown = (display + " " + sender_addr).lower()
        spoof = False
        for brand, real in BRANDS.items():
            if brand in display.lower() and sender_domain not in real:
                add("danger", f"Sender pretends to be '{brand}'",
                    f"The name says '{brand}' but the email comes from '{sender_domain}'.", 25)
                spoof = True
                break
        if not spoof and sender_domain in FREE_PROVIDERS and any(w in display.lower() for w in ORG_WORDS):
            add("warning", "Company name from a free email address",
                f"'{display}' is sending from {sender_domain}. Real companies use their own domain.", 12)

    # --- links (scored by the trained URL model) ---
    links, seen = [], set()
    for raw in URL_RE.findall(text):
        url = raw.rstrip(".,;:!?")
        if url.lower() in seen:
            continue
        seen.add(url.lower())
        if len(links) >= 8:
            break
        try:
            r = analyze_url(url)
            links.append({"url": url[:120], "host": r["host"], "risk_score": r["risk_score"], "level": r["level"]})
        except Exception:
            continue
    if links:
        worst = max(links, key=lambda l: l["risk_score"])
        if worst["risk_score"] >= 65:
            add("danger", "Dangerous link found", f"{worst['host']} scored {worst['risk_score']}% risk on the URL model.", 30)
        elif worst["risk_score"] >= 35:
            add("warning", "Suspicious link found", f"{worst['host']} scored {worst['risk_score']}% risk on the URL model.", 15)
        else:
            add("safe", "Links look normal", f"{len(links)} link(s) checked, none looked risky.")

    if not any(f["type"] in ("danger", "warning") for f in factors):
        add("safe", "No phishing patterns found", "The text has no urgent demands, requests for secrets or suspicious links.")

    score = min(100, points)
    level = level_for(score)
    verdict = {"LOW": "Looks safe", "MEDIUM": "Be careful", "HIGH": "Likely phishing"}[level]
    return {
        "kind": "email",
        "subject": subject,
        "sender": sender_addr or display,
        "risk_score": score,
        "level": level,
        "verdict": verdict,
        "factors": factors,
        "links": links,
        "word_count": len(words),
    }

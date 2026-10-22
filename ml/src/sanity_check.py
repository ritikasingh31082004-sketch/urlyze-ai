import joblib
from features import extract_features

bundle = joblib.load("../models/urlyze_model.joblib")
model, feats = bundle["model"], bundle["features"]

urls = [
    "https://www.google.com",
    "https://github.com/anthropics",
    "https://en.wikipedia.org/wiki/Phishing",
    "https://accounts.google.com/signin",
    "http://example.com",
    "http://paypal-secure-login.xyz/verify",
    "http://192.168.4.7/bank/login.php",
    "https://secure-update-account.top/confirm",
    "https://paypa1.com-verify.tk/signin",
    "http://bit.ly/3xYz",
]
for u in urls:
    f = extract_features(u)
    p = model.predict_proba([[f[n] for n in feats]])[0][1]
    print(f"{p:6.2f}  {u}")

"""Seed a few demo targets. Run: python -m app.seed"""
from app.database.db import init_db, SessionLocal
from app.database.models import Target

DEMO = [
    ("https://example.com", "baseline (should be clean-ish)"),
    ("https://expired.badssl.com", "expired TLS demo"),
    ("https://wrong.host.badssl.com", "TLS hostname mismatch demo"),
]


def main():
    init_db()
    db = SessionLocal()
    try:
        for url, label in DEMO:
            if not db.query(Target).filter(Target.url == url).first():
                db.add(Target(url=url, label=label))
        db.commit()
        print("seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

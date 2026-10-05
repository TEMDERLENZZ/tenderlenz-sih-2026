"""
Seed demo users for Phase 7.
Run this after users table is created.
"""
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.services.auth.password import hash_password


def seed_demo_users(db: Session):
    """
    Create demo users if they don't exist:
    - officer1 (OFFICER role)
    - bidder1 (BIDDER role)
    """
    # Check if users already exist
    existing_officer = db.query(User).filter(User.username == "officer1").first()
    existing_bidder = db.query(User).filter(User.username == "bidder1").first()

    users_created = []

    if not existing_officer:
        officer_user = User(
            username="officer1",
            password_hash=hash_password("demo123"),
            role=UserRole.OFFICER,
            is_active=True
        )
        db.add(officer_user)
        users_created.append("officer1 (OFFICER)")

    if not existing_bidder:
        bidder_user = User(
            username="bidder1",
            password_hash=hash_password("demo123"),
            role=UserRole.BIDDER,
            is_active=True
        )
        db.add(bidder_user)
        users_created.append("bidder1 (BIDDER)")

    if users_created:
        db.commit()
        print(f"[SUCCESS] Created demo users: {', '.join(users_created)}")
    else:
        print("[INFO] Demo users already exist")

    return users_created

from app.database import SessionLocal
from app.models.role import Role
from app.models.user import User
from app.core.security import hash_password


def create_admin(email: str, name: str, password: str) -> None:
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError(f"User with email '{email}' already exists.")

        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        if admin_role is None:
            admin_role = Role(name="Admin")
            db.add(admin_role)
            db.flush()

        admin = User(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            role_id=admin_role.id,
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"Admin created successfully: {admin.email}")
        print(f"Admin ID: {admin.id}")
        print(f"Role ID: {admin.role_id}")
    except Exception as exc:
        db.rollback()
        raise exc
    finally:
        db.close()


if __name__ == "__main__":
    admin_name = input("Enter admin full name: ").strip()
    admin_email = input("Enter admin email: ").strip()
    admin_password = input("Enter admin password: ").strip()

    create_admin(admin_email, admin_name, admin_password)

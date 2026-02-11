import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import engine, get_db
from app.models.user import User
from app.core import security
import getpass

async def create_superuser():
    print("--- Sugarclass Superuser Setup ---")
    email = input("Email: ")
    full_name = input("Full Name: ")
    password = getpass.getpass("Password: ")
    confirm_password = getpass.getpass("Confirm Password: ")

    if password != confirm_password:
        print("Error: Passwords do not match.")
        return

    async with AsyncSession(engine) as db:
        # Check if user already exists
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalars().first()

        if user:
            print(f"User {email} already exists. Elevating to Superuser...")
            user.is_superuser = True
            user.hashed_password = security.get_password_hash(password)
        else:
            print(f"Creating new superuser {email}...")
            user = User(
                email=email,
                full_name=full_name,
                hashed_password=security.get_password_hash(password),
                is_superuser=True,
                is_active=True
            )
            db.add(user)

        await db.commit()
        print(f"Success! {email} is now a superuser.")

if __name__ == "__main__":
    asyncio.run(create_superuser())

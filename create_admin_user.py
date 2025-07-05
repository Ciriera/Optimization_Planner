import asyncio
import traceback
from app.db.base import async_session
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy import select

async def create_admin_user():
    """Admin kullanıcısı oluştur"""
    try:
        async with async_session() as db:
            # Önce admin kullanıcısının var olup olmadığını kontrol et
            result = await db.execute(select(User.id, User.email, User.full_name, User.role, 
                                           User.hashed_password, User.is_active, User.is_superuser)
                                    .filter(User.email == "admin@example.com"))
            admin_user = result.first()
            
            if admin_user:
                print("Admin kullanıcısı zaten mevcut.")
                print(f"ID: {admin_user.id}, Email: {admin_user.email}, Role: {admin_user.role}")
                print(f"Hashed password: {admin_user.hashed_password}")
                return
            
            # Admin kullanıcısı yoksa oluştur
            admin = User(
                email="admin@example.com",
                full_name="Admin User",
                role=UserRole.ADMIN,
                hashed_password=get_password_hash("admin"),
                is_active=True,
                is_superuser=True
            )
            
            db.add(admin)
            await db.commit()
            await db.refresh(admin)
            print(f"Admin kullanıcısı oluşturuldu: {admin.id}")
            
            print("Veritabanındaki kullanıcılar:")
            users = await db.execute(select(User.id, User.email, User.role))
            for user in users.all():
                print(f"ID: {user.id}, Email: {user.email}, Role: {user.role}")
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(create_admin_user()) 
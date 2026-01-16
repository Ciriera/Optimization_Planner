"""
Script to seed additional classrooms into the database
Run this to add D224, D225, D226 classrooms for 8-9-10 classroom support
"""
import asyncio
import sys
import platform

# Add the app directory to the path
sys.path.insert(0, '.')

# Windows-specific event loop fix
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def seed_new_classrooms():
    from sqlalchemy import text
    from app.db.base import engine, async_session
    
    new_classrooms = [
        {"name": "D224", "capacity": 25, "location": "Bilgisayar Mühendisliği Binası"},
        {"name": "D225", "capacity": 25, "location": "Bilgisayar Mühendisliği Binası"},
        {"name": "D226", "capacity": 25, "location": "Bilgisayar Mühendisliği Binası"},
    ]
    
    async with async_session() as db:
        for classroom in new_classrooms:
            # Check if exists
            result = await db.execute(
                text(f"SELECT id FROM classrooms WHERE name = :name"),
                {"name": classroom["name"]}
            )
            existing = result.scalar()
            
            if existing:
                print(f"Classroom {classroom['name']} already exists (id={existing}), skipping...")
            else:
                # Insert new classroom
                await db.execute(
                    text("""
                        INSERT INTO classrooms (name, capacity, location, is_active) 
                        VALUES (:name, :capacity, :location, true)
                    """),
                    classroom
                )
                print(f"Created classroom: {classroom['name']}")
        
        await db.commit()
        
        # Verify total classrooms
        result = await db.execute(text("SELECT COUNT(*) FROM classrooms"))
        total = result.scalar()
        print(f"\nTotal classrooms in database: {total}")
        
        # List all classrooms
        result = await db.execute(text("SELECT id, name FROM classrooms ORDER BY id"))
        rows = result.fetchall()
        print("\nAll classrooms:")
        for row in rows:
            print(f"  {row[0]}: {row[1]}")

if __name__ == "__main__":
    asyncio.run(seed_new_classrooms())
    print("\nDone! You can now use 8, 9, or 10 classrooms.")

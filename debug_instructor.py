"""
Debug script for Instructor model
"""
import sys
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the models
from app.models.instructor import Instructor, InstructorType
from app.db.base import Base

def main():
    """Main function"""
    try:
        # Create an in-memory SQLite database
        engine = create_engine("sqlite:///:memory:", echo=True)
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Create a session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Print the Instructor model definition
        print("Instructor model definition:")
        print(f"  __tablename__: {Instructor.__tablename__}")
        print(f"  columns: {[c.name for c in Instructor.__table__.columns]}")
        print(f"  relationships: {[r for r in Instructor.__mapper__.relationships.keys()]}")
        
        # Try to create an Instructor object
        print("\nCreating Instructor object...")
        instructor = Instructor(
            name="Test Instructor",
            type="instructor",
            department="Computer Engineering",
            bitirme_count=0,
            ara_count=0,
            total_load=0
        )
        print(f"  instructor: {instructor}")
        
        # Add the instructor to the session
        session.add(instructor)
        session.commit()
        
        # Query the instructor
        print("\nQuerying Instructor object...")
        instructor = session.query(Instructor).first()
        print(f"  instructor: {instructor}")
        print(f"  instructor.name: {instructor.name}")
        print(f"  instructor.type: {instructor.type}")
        print(f"  instructor.department: {instructor.department}")
        
        print("\nDebug completed successfully")
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 
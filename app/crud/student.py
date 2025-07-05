from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate
from app.core.security import get_password_hash, verify_password

class CRUDStudent(CRUDBase[Student, StudentCreate, StudentUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[Student]:
        return db.query(Student).filter(Student.email == email).first()

    def get_by_student_number(self, db: Session, *, student_number: str) -> Optional[Student]:
        return db.query(Student).filter(Student.student_number == student_number).first()

    def create(self, db: Session, *, obj_in: StudentCreate) -> Student:
        db_obj = Student(
            email=obj_in.email,
            full_name=obj_in.full_name,
            student_number=obj_in.student_number,
            department=obj_in.department,
            gpa=obj_in.gpa,
            interests=obj_in.interests,
            hashed_password=get_password_hash(obj_in.password),
            is_active=True
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Student, obj_in: Union[StudentUpdate, Dict[str, Any]]
    ) -> Student:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[Student]:
        student = self.get_by_email(db, email=email)
        if not student:
            return None
        if not verify_password(password, student.hashed_password):
            return None
        return student

    def is_active(self, student: Student) -> bool:
        return student.is_active

    def get_available_students(self, db: Session) -> List[Student]:
        """Get students not assigned to any project"""
        return (
            db.query(Student)
            .filter(Student.is_active == True)
            .all()
        )

student = CRUDStudent(Student) 
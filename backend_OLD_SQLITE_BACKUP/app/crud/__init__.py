from app.crud.instructor import crud_instructor
from app.crud.project import crud_project
from app.crud.audit_log import crud_audit_log
from app.crud.algorithm import crud_algorithm
from app.crud.classroom import crud_classroom
from app.crud.timeslot import crud_timeslot
from app.crud.schedule import crud_schedule
from app.crud.user import user

# Alias'lar ekleyelim
project = crud_project
instructor = crud_instructor
audit_log = crud_audit_log
algorithm = crud_algorithm
classroom = crud_classroom
timeslot = crud_timeslot
schedule = crud_schedule 
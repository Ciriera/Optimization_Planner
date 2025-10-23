from app.db.session import SessionLocal
from app.models.classroom import Classroom


def ensure_classrooms(names):
	"""Ensure each classroom name in names exists; create if missing."""
	db = SessionLocal()
	try:
		created = []
		existing = {c.name for c in db.query(Classroom).all()}
		for name in names:
			if name not in existing:
				db.add(Classroom(name=name, capacity=30))
				db.commit()
				created.append(name)
		print({
			"existing": sorted(list(existing)),
			"created": created,
			"final": [c.name for c in db.query(Classroom).all()],
		})
	finally:
		db.close()


if __name__ == "__main__":
	ensure_classrooms(["D-106", "D-107", "D-108"])

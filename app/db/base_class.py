from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr

@as_declarative()
class Base:
    """
    SQLAlchemy için temel model sınıfı.
    Tüm modeller bu sınıftan türetilir.
    """
    id: Any
    __name__: str

    # Tablo adını otomatik olarak sınıf adından türet
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() 
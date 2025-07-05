from pydantic import BaseModel

class Msg(BaseModel):
    """
    Basit mesaj şeması
    """
    msg: str 
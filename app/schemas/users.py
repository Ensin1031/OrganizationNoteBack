from pydantic import BaseModel, Field, ConfigDict


class UserRead(BaseModel):
    """ для GET """
    id: int
    name: str
    login: str
    email: str
    verified: bool
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """ для POST """
    name: str
    login: str
    email: str
    password: str

    model_config = ConfigDict(extra="forbid")


class UserUpdate(BaseModel):
    """ для PATCH """
    name: str | None = None
    login: str | None = None
    email: str | None = None
    password: str | None = None

    model_config = ConfigDict(extra="forbid")


class UserPut(BaseModel):
    """ для PUT """
    name: str
    login: str
    email: str
    password: str

    model_config = ConfigDict(extra="forbid")

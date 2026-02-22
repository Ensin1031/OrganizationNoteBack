import enum


class GenderType(enum.IntEnum):

    UNSET = 0
    MALE = 1
    FEMALE = 2

    @property
    def label(self) -> str:
        return {
            GenderType.UNSET: "Не выбран",
            GenderType.MALE: "Мужской",
            GenderType.FEMALE: "Женский",
        }[self]

import math
from dataclasses import dataclass
from typing import Mapping

FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")

EMPTY = "กรุณากรอกค่านี้"
NOT_NUMBER = "ต้องเป็นตัวเลข"
NOT_FINITE = "ต้องเป็นตัวเลขจำกัด"
MUST_BE_POSITIVE = "ต้องมากกว่า 0"
BETA_POSITIVE = "beta ต้องมากกว่า 0"
VBE_NON_NEGATIVE = "VBE ต้องไม่ติดลบ"
VBE_BELOW_VCC = "VBE ต้องน้อยกว่า VCC"

POSITIVE_FIELDS = ("vcc", "r1", "r2", "rc", "re")


class BiasInputError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("; ".join(f"{field}: {message}" for field, message in errors.items()))


@dataclass(frozen=True)
class BiasInput:
    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float


def parse_inputs(raw: Mapping[str, str]) -> BiasInput:
    errors = {}
    values = {}

    for field in FIELDS:
        text = (raw.get(field) or "").strip()
        if not text:
            errors[field] = EMPTY
            continue
        try:
            number = float(text)
        except ValueError:
            errors[field] = NOT_NUMBER
            continue
        if not math.isfinite(number):
            errors[field] = NOT_FINITE
            continue
        values[field] = number

    for field in POSITIVE_FIELDS:
        if field in values and values[field] <= 0:
            errors[field] = MUST_BE_POSITIVE

    if "beta" in values and values["beta"] <= 0:
        errors["beta"] = BETA_POSITIVE

    if "vbe" in values:
        if values["vbe"] < 0:
            errors["vbe"] = VBE_NON_NEGATIVE
        elif "vcc" in values and values["vbe"] >= values["vcc"]:
            errors["vbe"] = VBE_BELOW_VCC

    if errors:
        raise BiasInputError(errors)

    return BiasInput(**values)

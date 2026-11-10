import math
from dataclasses import dataclass
from typing import Mapping

FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")

EMPTY = "This field is required."
NOT_NUMBER = "Enter a number."
NOT_FINITE = "Enter a finite number."
MUST_BE_POSITIVE = "Must be greater than 0."
BETA_POSITIVE = "beta must be greater than 0."
VBE_NON_NEGATIVE = "VBE cannot be negative."
VBE_BELOW_VCC = "VBE must be less than VCC."

POSITIVE_FIELDS = ("vcc", "r1", "r2", "rc", "re")

UNIT_FACTORS = {
    "vcc": {"V": 1.0, "mV": 1e-3},
    "r1": {"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6},
    "r2": {"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6},
    "rc": {"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6},
    "re": {"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6},
    "beta": {},
    "vbe": {"V": 1.0, "mV": 1e-3},
}

VCE_SAT = 0.2

W_CUTOFF = "Cutoff: VBB ≤ VBE, the transistor is off."
W_SAT = (
    "Saturation: VCE is below 0.2 V, so the values assume the active region "
    "and are only approximate."
)
W_STIFF = "The divider is not stiff: its current is less than 10× IB, so the bias point depends on beta."
W_DISAGREE = "The two methods disagree beyond tolerance — check the formulas in bias.py."


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
        values[field] = number * UNIT_FACTORS[field].get(raw.get(f"{field}_unit", ""), 1.0)

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


@dataclass(frozen=True)
class OperatingPoint:
    vb: float
    ve: float
    vc: float
    vce: float
    ib: float
    ic: float
    ie: float


@dataclass(frozen=True)
class BiasResult:
    region: str
    warnings: tuple[str, ...]
    primary: OperatingPoint
    independent: OperatingPoint | None = None
    agreement_ok: bool | None = None


def _thevenin(data: BiasInput) -> OperatingPoint:
    vbb = data.vcc * data.r2 / (data.r1 + data.r2)
    rb = data.r1 * data.r2 / (data.r1 + data.r2)
    ib = (vbb - data.vbe) / (rb + (data.beta + 1) * data.re)
    ic = data.beta * ib
    ie = (data.beta + 1) * ib
    ve = ie * data.re
    vb = data.vbe + ve
    vc = data.vcc - ic * data.rc
    return OperatingPoint(vb=vb, ve=ve, vc=vc, vce=vc - ve, ib=ib, ic=ic, ie=ie)


def _nodal(data: BiasInput) -> OperatingPoint:
    conductance = 1 / data.r1 + 1 / data.r2
    ve = (data.vcc / data.r1 - data.vbe * conductance) / (
        conductance + 1 / ((data.beta + 1) * data.re)
    )
    ie = ve / data.re
    ib = ie / (data.beta + 1)
    ic = data.beta * ib
    vb = ve + data.vbe
    vc = data.vcc - ic * data.rc
    return OperatingPoint(vb=vb, ve=ve, vc=vc, vce=vc - ve, ib=ib, ic=ic, ie=ie)


def points_agree(a: OperatingPoint, b: OperatingPoint) -> bool:
    return all(
        math.isclose(getattr(a, field), getattr(b, field), rel_tol=1e-9, abs_tol=1e-12)
        for field in ("vb", "ve", "vc", "vce", "ib", "ic", "ie")
    )


def analyze_bias(data: BiasInput) -> BiasResult:
    vbb = data.vcc * data.r2 / (data.r1 + data.r2)

    if vbb <= data.vbe:
        point = OperatingPoint(
            vb=vbb, ve=0.0, vc=data.vcc, vce=data.vcc, ib=0.0, ic=0.0, ie=0.0
        )
        return BiasResult(region="cutoff", warnings=(W_CUTOFF,), primary=point)

    primary = _thevenin(data)
    independent = _nodal(data)
    warnings = []
    region = "active"

    if primary.vce < VCE_SAT:
        region = "saturation"
        warnings.append(W_SAT)

    if data.vcc / (data.r1 + data.r2) < 10 * primary.ib:
        warnings.append(W_STIFF)

    agreement_ok = points_agree(primary, independent)
    if not agreement_ok:
        warnings.append(W_DISAGREE)

    return BiasResult(
        region=region,
        warnings=tuple(warnings),
        primary=primary,
        independent=independent,
        agreement_ok=agreement_ok,
    )

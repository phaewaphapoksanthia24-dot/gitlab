import math

from flask import Flask, render_template, request

from bias import (
    FIELDS,
    MODE_DIVIDER,
    MODE_EMITTER,
    MODE_FIELDS,
    MODE_FIXED,
    MODES,
    W_CUTOFF,
    W_FORWARD_ACTIVE,
    W_SAT,
    BiasInputError,
    analyze_mode,
    parse_mode_inputs,
)

app = Flask(__name__)

MODE_LABELS = {
    MODE_DIVIDER: "Voltage Divider Bias",
    MODE_FIXED: "Fixed Bias",
    MODE_EMITTER: "Emitter Bias",
}

DEFAULT_VALUES = {
    MODE_DIVIDER: {
        "vcc": "12.0",
        "r1": "100",
        "r2": "22",
        "rc": "2.2",
        "re": "1.0",
        "beta": "100",
        "vbe": "0.70",
    },
    MODE_FIXED: {
        "vcc": "12.0",
        "rc": "2.2",
        "rb": "1000",
        "beta": "100",
        "vbe": "0.70",
    },
    MODE_EMITTER: {
        "vcc": "12.0",
        "rc": "2.2",
        "rb": "1000",
        "re": "1.0",
        "beta": "100",
        "vbe": "0.70",
    },
}

DEFAULT_UNITS = {
    "vcc": "V",
    "r1": "kΩ",
    "r2": "kΩ",
    "rc": "kΩ",
    "re": "kΩ",
    "rb": "kΩ",
    "beta": "",
    "vbe": "V",
}

FIELD_DEFS = {
    "vcc": {"name": "vcc", "label": "VCC", "hint": "Supply Voltage", "units": ("V", "mV")},
    "r1": {"name": "r1", "label": "R1", "hint": "Upper Divider", "units": ("Ω", "kΩ", "MΩ")},
    "r2": {"name": "r2", "label": "R2", "hint": "Lower Divider", "units": ("Ω", "kΩ", "MΩ")},
    "rc": {"name": "rc", "label": "RC", "hint": "Collector Resistor", "units": ("Ω", "kΩ", "MΩ")},
    "re": {"name": "re", "label": "RE", "hint": "Emitter Resistor", "units": ("Ω", "kΩ", "MΩ")},
    "rb": {"name": "rb", "label": "RB", "hint": "Base Resistor", "units": ("Ω", "kΩ", "MΩ")},
    "beta": {"name": "beta", "label": "β", "hint": "Current Gain", "units": ()},
    "vbe": {"name": "vbe", "label": "VBE", "hint": "Base-Emitter Voltage", "units": ("V", "mV")},
}


def fields_for_mode(mode):
    return tuple(FIELD_DEFS[field] for field in MODE_FIELDS[mode])

RESULT_ROWS = (
    ("VB", "vb"),
    ("VE", "ve"),
    ("VC", "vc"),
    ("VCE", "vce"),
    ("IB", "ib"),
    ("IC", "ic"),
    ("IE", "ie"),
)

COMPARISON_ROWS = (
    ("VB", "V", "vb", 1.0, "{:.2f}"),
    ("VE", "V", "ve", 1.0, "{:.2f}"),
    ("VC", "V", "vc", 1.0, "{:.2f}"),
    ("VCE", "V", "vce", 1.0, "{:.2f}"),
    ("IB", "µA", "ib", 1e6, "{:.1f}"),
    ("IC", "mA", "ic", 1e3, "{:.2f}"),
    ("IE", "mA", "ie", 1e3, "{:.2f}"),
)


def format_value(attribute, value):
    if attribute in ("vb", "ve", "vc", "vce"):
        return f"{value:.2f} V"
    if attribute == "ib":
        return f"{value * 1e6:.1f} µA"
    return f"{value * 1e3:.2f} mA"


def build_result_rows(result):
    return [
        {"label": label, "value": format_value(attribute, getattr(result.primary, attribute))}
        for label, attribute in RESULT_ROWS
    ]


def build_comparison_rows(result):
    rows = []
    for label, unit, attribute, scale, number_format in COMPARISON_ROWS:
        primary = getattr(result.primary, attribute) * scale
        nodal = getattr(result.independent, attribute) * scale
        if math.isclose(primary, nodal, rel_tol=1e-9, abs_tol=1e-9):
            delta = "0"
        else:
            delta = f"{abs(primary - nodal):.2g}"
        rows.append(
            {
                "label": label,
                "unit": unit,
                "thevenin": number_format.format(primary),
                "nodal": number_format.format(nodal),
                "delta": delta,
            }
        )
    return rows


def region_info(result):
    vce = result.primary.vce
    if W_FORWARD_ACTIVE in result.warnings:
        return {
            "kind": "warn",
            "title": "Forward Active model may not apply",
            "detail": (
                f"IB = {result.primary.ib * 1e6:.1f} µA and VCE = {vce:.2f} V; "
                "the values come from the active-region equations and are only approximate."
            ),
        }
    if result.region == "active":
        return {
            "kind": "ok",
            "title": "Active region approximation OK",
            "detail": f"VCE = {vce:.2f} V > 0.2 V (transistor in active region)",
        }
    if result.region == "saturation":
        return {
            "kind": "warn",
            "title": "Saturation region",
            "detail": f"VCE = {vce:.2f} V ≤ 0.2 V — active-region values are approximate",
        }
    return {
        "kind": "off",
        "title": "Cutoff region",
        "detail": "VBB ≤ VBE — the transistor is off and no collector current flows",
    }


def schematic_labels(values, units):
    labels = {}
    for field in FIELDS:
        value = (values.get(field) or "").strip()
        unit = (units.get(field) or "").strip()
        labels[field] = f"{value} {unit}".strip() if value else "—"
    return labels


def render_page(
    values,
    units,
    mode=MODE_DIVIDER,
    mode_error=None,
    errors=None,
    result=None,
    warnings=(),
):
    return render_template(
        "index.html",
        values=values,
        units=units,
        mode=mode,
        mode_label=MODE_LABELS[mode],
        mode_labels=MODE_LABELS,
        mode_error=mode_error,
        errors=errors or {},
        fields=fields_for_mode(mode),
        result=result,
        rows=build_result_rows(result) if result else [],
        comparison=build_comparison_rows(result) if result and result.independent else [],
        region=region_info(result) if result else None,
        warnings=list(warnings),
        schematic=schematic_labels(values, units) if mode == MODE_DIVIDER else None,
    )


@app.get("/")
def index():
    mode = request.args.get("mode", MODE_DIVIDER)
    mode_error = None
    if mode not in MODES:
        mode_error = "Choose a valid bias mode."
        mode = MODE_DIVIDER
    return render_page(
        DEFAULT_VALUES[mode], DEFAULT_UNITS, mode=mode, mode_error=mode_error
    )


@app.post("/calculate")
def calculate():
    mode = request.form.get("mode", MODE_DIVIDER)
    if mode not in MODES:
        return render_page(
            DEFAULT_VALUES[MODE_DIVIDER],
            DEFAULT_UNITS,
            mode=MODE_DIVIDER,
            mode_error="Choose a valid bias mode.",
        )

    fields = MODE_FIELDS[mode]
    values = {field: request.form.get(field, "") for field in fields}
    units = {field: request.form.get(f"{field}_unit", "") for field in fields}
    raw = dict(values)
    raw.update({f"{field}_unit": units[field] for field in fields})

    try:
        data = parse_mode_inputs(raw, mode)
    except BiasInputError as error:
        return render_page(values, units, mode=mode, errors=error.errors)

    result = analyze_mode(data)
    extra_warnings = [
        w for w in result.warnings if w not in (W_CUTOFF, W_SAT, W_FORWARD_ACTIVE)
    ]
    return render_page(values, units, mode=mode, result=result, warnings=extra_warnings)


if __name__ == "__main__":
    app.run(debug=False, port=5000)

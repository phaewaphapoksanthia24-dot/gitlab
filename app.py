from flask import Flask, render_template, request

from bias import FIELDS, BiasInputError, analyze_bias, parse_inputs

app = Flask(__name__)

REGION_LABELS = {
    "cutoff": "Cutoff (ไม่นำกระแส)",
    "active": "Active",
    "saturation": "Saturation",
}

_ROW_SPEC = (
    ("VB", "V", "vb", 1.0),
    ("VE", "V", "ve", 1.0),
    ("VC", "V", "vc", 1.0),
    ("VCE", "V", "vce", 1.0),
    ("IB", "µA", "ib", 1e6),
    ("IC", "mA", "ic", 1e3),
    ("IE", "mA", "ie", 1e3),
)


def build_rows(result):
    rows = []
    for label, unit, attribute, scale in _ROW_SPEC:
        primary = getattr(result.primary, attribute) * scale
        if result.independent is None:
            independent = "—"
            delta = "—"
        else:
            other = getattr(result.independent, attribute) * scale
            independent = f"{other:.4g}"
            delta = f"{abs(primary - other):.2g}"
        rows.append(
            {
                "label": label,
                "unit": unit,
                "primary": f"{primary:.4g}",
                "independent": independent,
                "delta": delta,
            }
        )
    return rows


@app.get("/")
def index():
    return render_template(
        "index.html", values={}, errors={}, result=None, rows=[], region_label=None
    )


@app.post("/calculate")
def calculate():
    raw = {field: request.form.get(field, "") for field in FIELDS}
    try:
        data = parse_inputs(raw)
    except BiasInputError as error:
        return render_template(
            "index.html",
            values=raw,
            errors=error.errors,
            result=None,
            rows=[],
            region_label=None,
        )

    result = analyze_bias(data)
    return render_template(
        "index.html",
        values=raw,
        errors={},
        result=result,
        rows=build_rows(result),
        region_label=REGION_LABELS[result.region],
    )


if __name__ == "__main__":
    app.run(debug=False, port=5000)

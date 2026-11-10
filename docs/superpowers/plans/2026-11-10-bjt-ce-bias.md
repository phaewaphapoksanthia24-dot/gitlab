# BJT Common-Emitter DC Bias Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เว็บแอป Flask หน้าเดียวที่คำนวณจุดทำงาน DC ของวงจรไบอัส Common-Emitter ด้วยสองวิธีอิสระ แสดงผลเทียบกัน พร้อม validation และคำเตือนโหมดการทำงาน

**Architecture:** `bias.py` ถือสูตรวิศวกรรมทั้งหมด (validation, Thevenin, nodal, region, warnings) และคืนค่า SI ล้วน `app.py` แปลงเป็นหน่วยที่แสดงผลและส่งให้ Jinja template ผ่าน `build_rows()` เทสต์ logic ไม่ต้องใช้ Flask, เทสต์ route ใช้ Flask test client

**Tech Stack:** Python 3.10.11, Flask 3.x, `unittest` (ไม่ใช้ pytest), Jinja2, CSS ไฟล์เดียว ไม่มี JavaScript

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md`

## Global Constraints

- Python 3.10.11 บน Windows, shell เป็น PowerShell — คำสั่งรันใช้ `.venv\Scripts\python`
- dependency ตัวเดียวที่อนุญาต: Flask (`Flask>=3.0,<4`) — ห้ามเพิ่ม pytest หรือ library อื่น
- เทสต์ใช้ `unittest` เท่านั้น รันด้วย `.venv\Scripts\python -m unittest discover -v` จาก root repo
- ค่าใน `bias.py` เป็น SI ล้วน: แรงดันเป็น V, กระแสเป็น A, ความต้านทานเป็น Ω
- หน่วยที่แสดงผล: VB/VE/VC/VCE เป็น V, IB เป็น µA, IC/IE เป็น mA, ปัด 4 significant figures (`:.4g`)
- `VCE_SAT = 0.2` V, tolerance ตรงกัน `rel_tol=1e-9, abs_tol=1e-12`
- UI เป็นภาษาไทย ตัวแปร/ฟังก์ชันเป็นภาษาอังกฤษ, ไม่มี JavaScript, ไม่มี endpoint อื่นนอกจาก `GET /` และ `POST /calculate`
- ห้ามแก้ `electrical.py` หรือ `test_electrical.py`
- ข้อความ error/warning ต้องตรงตามที่ระบุใน plan ทุกตัวอักษร (เทสต์ assert ตรง ๆ)

## Review Focus

1. ผู้ใช้พิมพ์ตัวเลขแบบมีคอมมา (`47,000`) → ต้องขึ้น error "ต้องเป็นตัวเลข" ไม่ใช่ crash หรือตีความผิด
2. POST ที่ไม่มีฟิลด์นั้นมาเลย (ไม่ใช่แค่ค่าว่าง) → ต้องขึ้น "กรุณากรอกค่านี้"
3. ค่ามหาศาลจนล้นเป็น `inf` (`1e309`) → ต้องถูกปฏิเสธ ไม่คำนวณต่อ
4. `beta` เป็นทศนิยม (`100.5`) → ต้องยอมรับ ไม่ปฏิเสธ
5. กรอกผิดบางช่อง → ช่องที่กรอกถูกต้องต้องคงค่าไว้หลัง submit ไม่ถูกล้าง

---

### Task 1: Validation layer

**Files:**
- Create: `bias.py`
- Create: `tests/__init__.py` (ไฟล์ว่าง)
- Test: `tests/test_bias.py`

**Interfaces:**
- Consumes: ไม่มี
- Produces:
  - `FIELDS: tuple[str, ...]` = `("vcc", "r1", "r2", "rc", "re", "beta", "vbe")`
  - `BiasInputError(ValueError)` มี attribute `errors: dict[str, str]` (ชื่อฟิลด์ → ข้อความ)
  - `BiasInput` เป็น `@dataclass(frozen=True)` มี float fields: `vcc, r1, r2, rc, re, beta, vbe`
  - `parse_inputs(raw: Mapping[str, str]) -> BiasInput`

- [ ] **Step 1: เขียนเทสต์ที่จะ fail**

สร้าง `tests/__init__.py` (ว่าง) และ `tests/test_bias.py`:

```python
import unittest

from bias import BiasInputError, parse_inputs

VALID = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "4700",
    "re": "1000",
    "beta": "100",
    "vbe": "0.7",
}


def errors_for(**overrides):
    raw = dict(VALID, **overrides)
    with unittest.TestCase().assertRaises(BiasInputError) as ctx:
        parse_inputs(raw)
    return ctx.exception.errors


class TestParseInputs(unittest.TestCase):
    def test_valid_inputs_become_floats(self):
        data = parse_inputs(VALID)
        self.assertEqual(data.vcc, 12.0)
        self.assertEqual(data.r1, 47000.0)
        self.assertEqual(data.beta, 100.0)

    def test_missing_field_is_reported(self):
        raw = dict(VALID)
        del raw["rc"]
        with self.assertRaises(BiasInputError) as ctx:
            parse_inputs(raw)
        self.assertEqual(ctx.exception.errors["rc"], "กรุณากรอกค่านี้")

    def test_empty_field_is_reported(self):
        self.assertEqual(errors_for(r1="   ")["r1"], "กรุณากรอกค่านี้")

    def test_non_numeric_field_is_reported(self):
        self.assertEqual(errors_for(vcc="สิบสอง")["vcc"], "ต้องเป็นตัวเลข")

    def test_comma_separated_number_is_rejected(self):
        self.assertEqual(errors_for(r1="47,000")["r1"], "ต้องเป็นตัวเลข")

    def test_non_finite_values_are_rejected(self):
        for value in ("nan", "inf", "1e309"):
            with self.subTest(value=value):
                self.assertEqual(errors_for(re=value)["re"], "ต้องเป็นตัวเลขจำกัด")

    def test_zero_and_negative_resistances_are_rejected(self):
        for field in ("r1", "r2", "rc", "re"):
            for value in ("0", "-1"):
                with self.subTest(field=field, value=value):
                    self.assertEqual(errors_for(**{field: value})[field], "ต้องมากกว่า 0")

    def test_non_positive_vcc_is_rejected(self):
        self.assertEqual(errors_for(vcc="0")["vcc"], "ต้องมากกว่า 0")

    def test_non_positive_beta_is_rejected(self):
        for value in ("0", "-5"):
            with self.subTest(value=value):
                self.assertEqual(errors_for(beta=value)["beta"], "beta ต้องมากกว่า 0")

    def test_negative_vbe_is_rejected(self):
        self.assertEqual(errors_for(vbe="-0.1")["vbe"], "VBE ต้องไม่ติดลบ")

    def test_vbe_must_be_below_vcc(self):
        self.assertEqual(errors_for(vbe="12")["vbe"], "VBE ต้องน้อยกว่า VCC")

    def test_all_errors_are_collected(self):
        errors = errors_for(vcc="0", beta="-1", vbe="abc")
        self.assertEqual(set(errors), {"vcc", "beta", "vbe"})

    def test_fractional_beta_is_accepted(self):
        self.assertEqual(parse_inputs(dict(VALID, beta="100.5")).beta, 100.5)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: รันเทสต์ให้เห็นว่า fail**

Run: `.venv\Scripts\python -m unittest -v tests.test_bias`
Expected: FAIL — `ModuleNotFoundError: No module named 'bias'`

(ถ้ายังไม่มี `.venv` ให้สร้างก่อน: `python -m venv .venv` แล้วใช้ `.venv\Scripts\python` ต่อจากนี้)

- [ ] **Step 3: เขียน `bias.py` ให้ผ่าน**

สร้าง `bias.py` ที่มี: import `math`, `Mapping`, `dataclass`, ค่าคงที่ข้อความ error ตามตัวอักษรในเทสต์, `FIELDS`, `BiasInputError`, `BiasInput`, `parse_inputs`

กติกาของ `parse_inputs` (ทำตามลำดับนี้ต่อฟิลด์):
1. `text = (raw.get(field) or "").strip()`; ว่าง → `"กรุณากรอกค่านี้"`
2. `float(text)` ผิด → `"ต้องเป็นตัวเลข"`
3. `math.isfinite(number)` เป็น False → `"ต้องเป็นตัวเลขจำกัด"`
4. เก็บค่าที่ parse ได้ไว้ใน dict ชั่วคราว

หลังวนครบทุกฟิลด์ แล้วตรวจช่วงเฉพาะฟิลด์ที่ parse ผ่าน:
- `vcc, r1, r2, rc, re` ≤ 0 → `"ต้องมากกว่า 0"`
- `beta` ≤ 0 → `"beta ต้องมากกว่า 0"`
- `vbe` < 0 → `"VBE ต้องไม่ติดลบ"`; ถ้า `vbe >= vcc` → `"VBE ต้องน้อยกว่า VCC"` (ตรวจข้อหลังเฉพาะเมื่อ `vcc` parse ผ่าน)

ถ้ามี error ใด ๆ → `raise BiasInputError(errors)`; ถ้าไม่มี → `BiasInput(**values)`

- [ ] **Step 4: รันเทสต์ให้ผ่าน**

Run: `.venv\Scripts\python -m unittest -v tests.test_bias`
Expected: PASS ทั้งหมด 13 เทสต์

- [ ] **Step 5: Commit**

```bash
git add bias.py tests/__init__.py tests/test_bias.py
git commit -m "feat: validate BJT bias inputs with per-field Thai errors"
```

---

### Task 2: Primary calculation, region detection, warnings

**Files:**
- Modify: `bias.py`
- Test: `tests/test_bias.py`

**Interfaces:**
- Consumes: `BiasInput` จาก Task 1
- Produces:
  - `VCE_SAT: float` = `0.2`
  - `OperatingPoint` เป็น `@dataclass(frozen=True)` มี float fields: `vb, ve, vc, vce, ib, ic, ie`
  - `BiasResult` เป็น `@dataclass(frozen=True)` มี fields: `region: str` (`"cutoff"|"active"|"saturation"`), `warnings: tuple[str, ...]`, `primary: OperatingPoint`, `independent: OperatingPoint | None`, `agreement_ok: bool | None`
  - `analyze_bias(data: BiasInput) -> BiasResult`
  - ข้อความ warning constants: `W_CUTOFF`, `W_SAT`, `W_STIFF`

- [ ] **Step 1: เขียนเทสต์ที่จะ fail**

เพิ่มใน `tests/test_bias.py`:

```python
from bias import BiasInput, analyze_bias


def make_input(**overrides):
    base = dict(vcc=12.0, r1=47000.0, r2=10000.0, rc=4700.0, re=1000.0, beta=100.0, vbe=0.7)
    base.update(overrides)
    return BiasInput(**base)


class TestPrimaryCalculation(unittest.TestCase):
    def test_active_region_values(self):
        result = analyze_bias(make_input())
        self.assertEqual(result.region, "active")
        self.assertAlmostEqual(result.primary.vb, 1.9991970451, delta=1e-9)
        self.assertAlmostEqual(result.primary.ve, 1.2991970451, delta=1e-9)
        self.assertAlmostEqual(result.primary.vc, 5.9542315722, delta=1e-9)
        self.assertAlmostEqual(result.primary.vce, 4.6550345271, delta=1e-9)
        self.assertAlmostEqual(result.primary.ib, 1.286330e-5, delta=1e-11)
        self.assertAlmostEqual(result.primary.ic, 1.286330e-3, delta=1e-9)
        self.assertAlmostEqual(result.primary.ie, 1.299197e-3, delta=1e-9)

    def test_active_region_has_no_warnings(self):
        self.assertEqual(analyze_bias(make_input()).warnings, ())

    def test_cutoff_clamps_currents_and_reports_zero(self):
        result = analyze_bias(make_input(vcc=5.0, r1=100000.0, r2=10000.0, rc=2200.0))
        self.assertEqual(result.region, "cutoff")
        self.assertAlmostEqual(result.primary.vb, 0.4545454545, delta=1e-9)
        self.assertEqual(result.primary.ve, 0.0)
        self.assertEqual(result.primary.vc, 5.0)
        self.assertEqual(result.primary.vce, 5.0)
        self.assertEqual(result.primary.ib, 0.0)
        self.assertEqual(result.primary.ic, 0.0)
        self.assertEqual(result.primary.ie, 0.0)
        self.assertIsNone(result.independent)
        self.assertIsNone(result.agreement_ok)
        self.assertIn("cutoff", result.warnings[0])

    def test_saturation_is_detected_and_values_stay_unclamped(self):
        result = analyze_bias(make_input(rc=10000.0))
        self.assertEqual(result.region, "saturation")
        self.assertAlmostEqual(result.primary.vce, -2.1625341256, delta=1e-9)
        self.assertAlmostEqual(result.primary.vc, -0.8633370805, delta=1e-9)
        self.assertTrue(any("saturation" in w for w in result.warnings))

    def test_non_stiff_divider_gets_a_warning(self):
        result = analyze_bias(make_input(r1=10000.0, r2=10000.0, rc=100.0, re=47.0))
        self.assertEqual(result.region, "active")
        self.assertTrue(any("10 เท่า" in w for w in result.warnings))

    def test_stiff_divider_gets_no_warning(self):
        self.assertFalse(any("10 เท่า" in w for w in analyze_bias(make_input()).warnings))
```

- [ ] **Step 2: รันเทสต์ให้เห็นว่า fail**

Run: `.venv\Scripts\python -m unittest -v tests.test_bias`
Expected: FAIL — `ImportError: cannot import name 'BiasInput' from 'bias'` (หรือ `analyze_bias`)

- [ ] **Step 3: เขียน implementation**

เพิ่มใน `bias.py` ตามสูตรใน spec หัวข้อ "วิธีคำนวณหลัก — Thevenin equivalent":

- `_thevenin(data) -> OperatingPoint` — คำนวณ `vbb`, `rb`, `ib`, `ic`, `ie`, `ve`, `vb = vbe + ve`, `vc = vcc - ic*rc`, `vce = vc - ve`
- `analyze_bias(data)`: คำนวณ `vbb = vcc*r2/(r1+r2)` ก่อน
  - ถ้า `vbb <= vbe` → `region="cutoff"`, `primary = OperatingPoint(vb=vbb, ve=0, vc=vcc, vce=vcc, ib=0, ic=0, ie=0)`, `independent=None`, `agreement_ok=None`, `warnings=(W_CUTOFF,)` แล้ว return ทันที
  - ไม่งั้น `primary = _thevenin(data)`; `region = "saturation"` + `W_SAT` ถ้า `primary.vce < VCE_SAT`; ถ้า `vcc/(r1+r2) < 10*primary.ib` เพิ่ม `W_STIFF`; `independent` และ `agreement_ok` ยังไม่ต้องใส่ (Task 3) — ใส่ `None` ไว้ก่อน

ข้อความ constants (ตรงตัวอักษร):
- `W_CUTOFF = "โหมด cutoff: VBB ≤ VBE ทรานซิสเตอร์ไม่นำกระแส"`
- `W_SAT = "โหมด saturation: VCE ต่ำกว่า 0.2 V ค่าที่แสดงมาจากสมมติฐาน active region จึงเป็นเพียงค่าประมาณ"`
- `W_STIFF = "กระแสในตัวแบ่งน้อยกว่า 10 เท่าของ IB จุดทำงานจึงไวต่อ beta"`

- [ ] **Step 4: รันเทสต์ให้ผ่าน**

Run: `.venv\Scripts\python -m unittest -v tests.test_bias`
Expected: PASS ทั้งหมด 19 เทสต์

- [ ] **Step 5: Commit**

```bash
git add bias.py tests/test_bias.py
git commit -m "feat: compute Thevenin operating point and flag bias region"
```

---

### Task 3: Independent nodal calculation and agreement check

**Files:**
- Modify: `bias.py`
- Test: `tests/test_bias.py`

**Interfaces:**
- Consumes: `OperatingPoint`, `BiasResult`, `analyze_bias`, `BiasInput`
- Produces:
  - `_nodal(data: BiasInput) -> OperatingPoint`
  - `points_agree(a: OperatingPoint, b: OperatingPoint) -> bool` — ใช้ `math.isclose(rel_tol=1e-9, abs_tol=1e-12)` กับทั้ง 7 ค่า
  - `analyze_bias` เติม `independent` และ `agreement_ok` ในโหมด active/saturation
  - `W_DISAGREE = "ผลจากสองวิธีไม่ตรงกันเกิน tolerance — ตรวจสอบสูตรใน bias.py"`

- [ ] **Step 1: เขียนเทสต์ที่จะ fail**

เพิ่มใน `tests/test_bias.py`:

```python
from bias import OperatingPoint, points_agree


class TestIndependentCalculation(unittest.TestCase):
    def test_independent_method_matches_known_values(self):
        result = analyze_bias(make_input())
        self.assertIsNotNone(result.independent)
        self.assertAlmostEqual(result.independent.ve, 1.2991970451, delta=1e-9)
        self.assertAlmostEqual(result.independent.vb, 1.9991970451, delta=1e-9)
        self.assertAlmostEqual(result.independent.vc, 5.9542315722, delta=1e-9)
        self.assertAlmostEqual(result.independent.ic, 1.286330e-3, delta=1e-9)

    def test_methods_agree_across_parameter_sweep(self):
        cases = [
            dict(),
            dict(beta=50.0),
            dict(beta=200.0),
            dict(vcc=22.0, r1=22000.0, r2=4700.0, rc=2200.0, re=470.0, beta=200.0, vbe=0.65),
            dict(rc=10000.0),
        ]
        for overrides in cases:
            with self.subTest(**overrides):
                result = analyze_bias(make_input(**overrides))
                self.assertIsNotNone(result.independent)
                self.assertTrue(result.agreement_ok)
                self.assertFalse(any("ไม่ตรงกัน" in w for w in result.warnings))

    def test_points_agree_rejects_mismatch(self):
        a = OperatingPoint(vb=1.0, ve=1.0, vc=1.0, vce=1.0, ib=1.0, ic=1.0, ie=1.0)
        b = OperatingPoint(vb=1.0, ve=1.0, vc=1.0, vce=1.0, ib=1.0, ic=1.0, ie=1.01)
        self.assertTrue(points_agree(a, a))
        self.assertFalse(points_agree(a, b))
```

- [ ] **Step 2: รันเทสต์ให้เห็นว่า fail**

Run: `.venv\Scripts\python -m unittest -v tests.test_bias`
Expected: FAIL — `ImportError: cannot import name 'OperatingPoint'` / `points_agree`

- [ ] **Step 3: เขียน implementation**

เพิ่ม `_nodal(data)` ตามสูตรใน spec หัวข้อ "วิธีอิสระ — nodal analysis" (คำนวณ `ve` จากสมการเดียว แล้วต่อ `ie`, `ib`, `ic`, `vb`, `vc`, `vce` — ห้ามใช้ `vbb`/`rb`)

เพิ่ม `points_agree(a, b)` เปรียบเทียบทั้ง 7 attributes ด้วย `math.isclose`

ใน `analyze_bias` (เฉพาะเส้นทางที่ไม่ใช่ cutoff): `independent = _nodal(data)`, `agreement_ok = points_agree(primary, independent)`, ถ้าไม่ตรงให้เพิ่ม `W_DISAGREE` ใน warnings

- [ ] **Step 4: รันเทสต์ให้ผ่าน**

Run: `.venv\Scripts\python -m unittest -v tests.test_bias`
Expected: PASS ทั้งหมด 22 เทสต์

- [ ] **Step 5: Commit**

```bash
git add bias.py tests/test_bias.py
git commit -m "feat: cross-check bias point with independent nodal analysis"
```

---

### Task 4: Flask form page, stylesheet, dependencies

**Files:**
- Create: `requirements.txt`
- Create: `app.py`
- Create: `templates/index.html`
- Create: `static/style.css`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `FIELDS`, `parse_inputs`, `BiasInputError`, `analyze_bias` จาก `bias.py`
- Produces:
  - `app: flask.Flask` (import ได้จาก `app`)
  - `GET /` คืนหน้า 200 ที่มี input ทั้ง 7 ชื่อ (`name="vcc"` … `name="vbe"`)
  - `GET /static/style.css` คืน 200

- [ ] **Step 1: ติดตั้ง dependency**

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install "Flask>=3.0,<4"
```

สร้าง `requirements.txt` บรรจุบรรทัดเดียว: `Flask>=3.0,<4`

- [ ] **Step 2: เขียนเทสต์ที่จะ fail**

สร้าง `tests/test_app.py`:

```python
import unittest

from app import app


class TestFormPage(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_returns_form_with_all_fields(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', body)

    def test_index_shows_title_and_units(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("BJT", body)
        self.assertIn("VCC", body)
        self.assertIn("µA", body)

    def test_stylesheet_is_served(self):
        self.assertEqual(self.client.get("/static/style.css").status_code, 200)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: รันเทสต์ให้เห็นว่า fail**

Run: `.venv\Scripts\python -m unittest -v tests.test_app`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 4: เขียน implementation**

`app.py`:
- `app = Flask(__name__)`
- `@app.get("/")` → `render_template("index.html", values={}, errors={}, result=None, rows=[], region_label=None)`
- ท้ายไฟล์: `if __name__ == "__main__": app.run(debug=False, port=5000)`

`templates/index.html` — ต้องมี:
- `<form method="post" action="/calculate">`
- 7 input โดยใช้ `name` ตรงกับ `FIELDS`, `value="{{ values.get('vcc', '') }}"` และใต้ input แต่ละตัวมี `{% if errors.get('vcc') %}<p class="error">{{ errors.get('vcc') }}</p>{% endif %}`
- label: `VCC (V)`, `R1 (Ω)`, `R2 (Ω)`, `RC (Ω)`, `RE (Ω)`, `beta`, `VBE (V)`
- หัวเรื่อง `BJT Common-Emitter DC Bias` และบรรทัดอธิบายว่าหน่วย IB เป็น µA, IC/IE เป็น mA
- `{% block %}` ไม่จำเป็น — ไฟล์เดียว ไม่ extends

`static/style.css` — ไฟล์เดียว จัดฟอร์มเป็น grid, ตารางผลมีเส้นตาราง, `.error` สีแดง, `.warning` สีส้ม, `.region` ตัวหนา ไม่ต้องมี framework

- [ ] **Step 5: รันเทสต์ให้ผ่าน**

Run: `.venv\Scripts\python -m unittest -v tests.test_app`
Expected: PASS ทั้งหมด 3 เทสต์

- [ ] **Step 6: Commit**

```bash
git add requirements.txt app.py templates/index.html static/style.css tests/test_app.py
git commit -m "feat: add Flask form page for BJT bias inputs"
```

---

### Task 5: Calculate route, comparison table, warnings

**Files:**
- Modify: `app.py`
- Modify: `templates/index.html`
- Modify: `static/style.css`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `parse_inputs`, `BiasInputError`, `analyze_bias`, `BiasResult`
- Produces:
  - `build_rows(result: BiasResult) -> list[dict]` — แต่ละ dict มี key `label`, `unit`, `primary`, `independent`, `delta` เป็น string ที่จัดรูปแบบแล้ว; เมื่อ `result.independent is None` ใช้ `"—"` ทั้งสองช่อง
  - `REGION_LABELS: dict[str, str]` = `{"cutoff": "Cutoff (ไม่นำกระแส)", "active": "Active", "saturation": "Saturation"}`
  - `POST /calculate`: สำเร็จ → 200 + ตารางผล; ผิด → 200 + error ใต้ช่อง + คงค่าเดิม

- [ ] **Step 1: เขียนเทสต์ที่จะ fail**

เพิ่มใน `tests/test_app.py`:

```python
VALID_FORM = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "4700",
    "re": "1000",
    "beta": "100",
    "vbe": "0.7",
}


class TestCalculateRoute(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def post(self, **overrides):
        data = dict(VALID_FORM, **overrides)
        return self.client.post("/calculate", data=data)

    def test_valid_post_shows_operating_point_and_comparison(self):
        body = self.post().get_data(as_text=True)
        self.assertIn("Active", body)
        self.assertIn("1.999", body)   # VB
        self.assertIn("12.86", body)   # IB เป็น µA
        self.assertIn("Thevenin", body)
        self.assertIn("Nodal", body)
        self.assertNotIn("class=\"error\"", body)

    def test_invalid_post_shows_error_and_keeps_valid_values(self):
        body = self.post(r1="0").get_data(as_text=True)
        self.assertIn("ต้องมากกว่า 0", body)
        self.assertIn('value="47000"', body)  # ค่าที่ถูกต้องช่องอื่นยังอยู่
        self.assertNotIn("Thevenin", body)

    def test_missing_field_shows_required_error(self):
        data = dict(VALID_FORM)
        del data["beta"]
        body = self.client.post("/calculate", data=data).get_data(as_text=True)
        self.assertIn("กรุณากรอกค่านี้", body)

    def test_cutoff_shows_note_instead_of_comparison(self):
        body = self.post(vcc="5", r1="100000", r2="10000", rc="2200").get_data(as_text=True)
        self.assertIn("Cutoff", body)
        self.assertIn("ไม่เทียบผล", body)
        self.assertNotIn("Thevenin", body)

    def test_saturation_shows_warning(self):
        body = self.post(rc="10000").get_data(as_text=True)
        self.assertIn("Saturation", body)
        self.assertIn("active region", body)

    def test_non_stiff_divider_shows_warning(self):
        body = self.post(r1="10000", r2="10000", rc="100", re="47").get_data(as_text=True)
        self.assertIn("10 เท่า", body)
```

- [ ] **Step 2: รันเทสต์ให้เห็นว่า fail**

Run: `.venv\Scripts\python -m unittest -v tests.test_app`
Expected: FAIL — `404` เพราะยังไม่มี route `POST /calculate` (หรือ `AssertionError` จาก `Thevenin` ไม่พบ)

- [ ] **Step 3: เขียน implementation**

`app.py` เพิ่ม:
- `REGION_LABELS` ตามที่ระบุ
- `_ROW_SPEC = (("VB","V","vb",1.0), ("VE","V","ve",1.0), ("VC","V","vc",1.0), ("VCE","V","vce",1.0), ("IB","µA","ib",1e6), ("IC","mA","ic",1e3), ("IE","mA","ie",1e3))`
- `build_rows(result)`: วน `_ROW_SPEC`, คูณด้วย scale, จัดรูป `f"{value:.4g}"`, delta = `f"{abs(p - q):.2g}"`
- `@app.post("/calculate")`:
  - `raw = {field: request.form.get(field, "") for field in FIELDS}`
  - `try: data = parse_inputs(raw)` → `except BiasInputError as error: return render_template("index.html", values=raw, errors=error.errors, result=None, rows=[], region_label=None)`
  - สำเร็จ: `result = analyze_bias(data)` แล้ว render ด้วย `values=raw, errors={}, result=result, rows=build_rows(result), region_label=REGION_LABELS[result.region]`

`templates/index.html` เพิ่มส่วนผลลัพธ์ (หลังฟอร์ม) — ต้องมี:
- `{% if result %}` … `{% endif %}`
- บรรทัดโหมด: `<p class="region">โหมดการทำงาน: {{ region_label }}</p>`
- `{% if result.independent %}` ตาราง `<table>` หัวคอลัมน์ `ค่า | หน่วย | Thevenin | Nodal | ต่าง` วน `rows`
- `{% else %}` (โหมด cutoff) `<p class="note">ไม่เทียบผล: วงจรอยู่ในโหมด cutoff</p>`
- `{% if result.warnings %}<ul class="warning">` วนแสดง warning
- คงค่าที่กรอกไว้ทุกช่องด้วย `values.get(...)` (มีอยู่แล้วจาก Task 4)

`static/style.css` เพิ่มสไตล์ `table`, `.note`, `.region`, `.warning`

- [ ] **Step 4: รันเทสต์ให้ผ่าน**

Run: `.venv\Scripts\python -m unittest -v tests.test_app`
Expected: PASS ทั้งหมด 9 เทสต์

- [ ] **Step 5: Commit**

```bash
git add app.py templates/index.html static/style.css tests/test_app.py
git commit -m "feat: render DC operating point comparison and region warnings"
```

---

### Task 6: README, full-suite verification, localhost demo, push

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: ทุกอย่างจาก Task 1–5
- Produces: README ที่ไม่มี conflict marker, เอกสารวิธีรัน, commit ที่ push ขึ้น `origin/main`

- [ ] **Step 1: แก้ README**

ลบ conflict marker ทั้งสามบรรทัด (`<<<<<<< HEAD`, `=======`, `>>>>>>> 42fcee8 ...`) โดย**เก็บเนื้อหาทั้งสองฝั่งไว้** ตามลำดับ:

1. `# gitlab` + `ใช้สำหรับเรียนแลปคอมโปรไฟฟ้า`
2. `## DC Circuit Calculator` + คำอธิบายวัตถุประสงค์ภาษาไทยเดิม (คงไว้ทั้งย่อหน้า)
3. `## BJT Common-Emitter DC Bias (ENG29 2121)` + 2–3 บรรทัดว่าคำนวณจุดทำงาน DC ด้วยสองวิธี (Thevenin กับ nodal) และเตือนโหมด cutoff/active/saturation
4. `### วิธีรัน` — โค้ดบล็อก:
   ```bash
   python -m venv .venv
   .venv\Scripts\python -m pip install -r requirements.txt
   .venv\Scripts\python app.py
   ```
   แล้วเปิด http://127.0.0.1:5000
5. `### วิธีรันเทสต์` — `.venv\Scripts\python -m unittest discover -v`

- [ ] **Step 2: รันเทสต์ทั้งหมด**

Run: `.venv\Scripts\python -m unittest discover -v`
Expected: PASS ทั้งหมด — 9 เทสต์เดิม (`test_electrical`) + 22 เทสต์ `test_bias` + 9 เทสต์ `test_app` = 40 เทสต์, `OK`

- [ ] **Step 3: ตรวจว่าแอปรันจริงบน localhost**

```powershell
$server = Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "app.py" -PassThru
Start-Sleep -Seconds 3
$response = Invoke-WebRequest http://127.0.0.1:5000 -UseBasicParsing
$response.StatusCode
$response.Content -match 'name="vcc"'
Stop-Process -Id $server.Id
```

Expected: `200` และ `True`

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: document BJT bias app setup and run steps"
```

- [ ] **Step 5: Push และตรวจสอบ**

```powershell
git push origin main
git status -sb
git rev-parse HEAD
git rev-parse origin/main
```

Expected: `git status -sb` ขึ้น `## main...origin/main` (ไม่มี ahead/behind), และ `HEAD` กับ `origin/main` เป็น SHA เดียวกัน

# BJT DC Bias Three Modes (Lab 03) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เพิ่มโหมด Fixed Bias และ Emitter Bias ให้เว็บ Flask เดิม โดยคงผล Voltage Divider เดิมไว้ทุกกรณี แล้วตรวจ A1–A5 ผ่าน Browser จริง

**Architecture:** `bias.py` ถือสูตรและ validation ทั้งสามโหมด (SI ล้วน) โดยไม่แก้ฟังก์ชัน Divider เดิม `app.py` เลือกช่อง/ฟังก์ชันตามโหมดและแปลงหน่วยแสดงผล `index.html` แสดงเฉพาะช่องของโหมดและ reload ฟอร์มเมื่อเปลี่ยนโหมดโดยไม่ใช้ JavaScript

**Tech Stack:** Python 3.12.7, Flask 3.x, `unittest` เดิม (ไม่เพิ่มเทสต์ใหม่), Jinja2, CSS ไฟล์เดียว, ไม่มี JavaScript

**Spec:** `docs/superpowers/specs/2026-11-17-bjt-bias-modes-design.md`

## Global Constraints

- Windows + PowerShell; venv ที่ `.venv` (ยังไม่มี ให้สร้างด้วย `python -m venv .venv`)
- dependency เดียวที่อนุญาต: `Flask>=3.0,<4`
- **ห้ามเพิ่มไฟล์ unittest ใหม่** (ใบงานกำหนดให้ตรวจผ่าน Browser) — แต่เทสต์เดิม 40 ตัวต้องผ่านทั้งหมด
- ห้ามแก้พฤติกรรม Voltage Divider เดิม (A1 ต้องได้ผลเท่า Lab 2)
- ค่าใน `bias.py` เป็น SI: V, A, Ω; แสดง VB/VE/VC/VCE เป็น V, IB เป็น µA, IC/IE เป็น mA
- endpoint มีแค่ `GET /` และ `POST /calculate`; ไม่มี JavaScript
- `mode` เริ่มต้นคือ `divider`; โหมดไม่รู้จักต้องแจ้ง error ไม่คำนวณเป็น Divider
- ห้ามแก้ `electrical.py` / `test_electrical.py`
- ข้อความ error เดิมต้องคงไว้ทุกตัวอักษร (เทสต์เดิม assert ตรง ๆ)

## Review Focus

1. `POST /calculate` ที่ไม่มีช่อง `mode` มาเลย → ต้องคำนวณ Divider เหมือน Lab 2 ทุกค่า
2. โหมดแปลก เช่น `mode=hfe` → ต้องขึ้น error และไม่มีผลลัพธ์ Divider โผล่มา
3. Fixed ต้องไม่บังคับ R1/R2/RE; Emitter ต้องไม่บังคับ R1/R2; แต่ขาด RB ต้องขึ้น error
4. `RB=0`, `RB=-1`, `RB=abc` → error ใต้ช่อง RB, เว็บไม่ล่ม, ไม่แสดงผลรอบก่อน
5. A3→A4 เปลี่ยนเฉพาะ RE 1k→2k → IC ต้องลดจาก 1.026340 เป็น 0.940100 mA (ไม่ใช่ผลค้าง)

---

### Task 1: Domain layer — mode input + Fixed/Emitter

**Files:**
- Modify: `bias.py`
- Test: `tests/test_bias.py`, `tests/test_app.py` (รันของเดิม ไม่แก้)

**Interfaces:**
- Consumes: `BiasInput`, `BiasInputError`, `OperatingPoint`, `BiasResult`, `analyze_bias`, `parse_inputs`, `VCE_SAT`, `UNIT_FACTORS`, และข้อความ error เดิมทั้งหมด
- Produces:
  - `MODE_DIVIDER = "divider"`, `MODE_FIXED = "fixed"`, `MODE_EMITTER = "emitter"`, `MODES = (MODE_DIVIDER, MODE_FIXED, MODE_EMITTER)`
  - `MODE_FIELDS: dict[str, tuple[str, ...]]` = `{"divider": ("vcc","r1","r2","rc","re","beta","vbe"), "fixed": ("vcc","rc","rb","beta","vbe"), "emitter": ("vcc","rc","rb","re","beta","vbe")}`
  - `ModeBiasInput` เป็น `@dataclass(frozen=True)` fields: `mode: str, vcc: float, rc: float, beta: float, vbe: float, r1: float | None = None, r2: float | None = None, re: float | None = None, rb: float | None = None`
  - `parse_mode_inputs(raw: Mapping[str, str], mode: str) -> ModeBiasInput`
  - `analyze_mode(data: ModeBiasInput) -> BiasResult`
  - `W_FORWARD_ACTIVE: str`

- [ ] **Step 1: เตรียม venv และยืนยัน baseline**

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m unittest discover -v
```

Expected: `OK` และผ่าน 40 เทสต์

- [ ] **Step 2: บันทึกค่า A1 ก่อนแก้โค้ด**

รัน one-off (ไม่ commit) ด้วย Flask test client กับฟอร์ม A1:

```powershell
@'
from app import app
data = {"vcc":"12","vcc_unit":"V","r1":"100","r1_unit":"kΩ","r2":"22","r2_unit":"kΩ","rc":"2.2","rc_unit":"kΩ","re":"1.0","re_unit":"kΩ","beta":"100","vbe":"0.70","vbe_unit":"V"}
body = app.test_client().post("/calculate", data=data).get_data(as_text=True)
print(body)
'@ | Set-Content -Encoding utf8 "$env:TEMP\a1_baseline.py"
.venv\Scripts\python "$env:TEMP\a1_baseline.py"
```

Expected ค่าที่เห็น: `VB 1.94 V`, `VE 1.24 V`, `VC 9.29 V`, `VCE 8.05 V`, `IC 1.23 mA` (ค่าอ้างอิงอิสระ: VB=1.942157, VE=1.242157, VC=9.294312, VCE=8.052155, IC=1.229858 mA)

- [ ] **Step 3: เพิ่ม `rb` unit factor และ mode constants/fields**

ใน `bias.py` เพิ่ม `"rb"` ใน `UNIT_FACTORS` ด้วย `{"Ω": 1.0, "kΩ": 1e3, "MΩ": 1e6}` และเพิ่ม constants/`MODE_FIELDS` ตาม Interfaces

- [ ] **Step 4: เขียน `parse_mode_inputs`**

- `mode` ไม่อยู่ใน `MODES` → `raise BiasInputError({"mode": "Choose a valid bias mode."})`
- วนเฉพาะ `MODE_FIELDS[mode]` ใช้กติกาเดิม: ว่าง → `EMPTY`, แปลงไม่ได้ → `NOT_NUMBER`, ไม่ finite → `NOT_FINITE`
- แปลงหน่วยด้วย `UNIT_FACTORS`
- ค่าบวก: `vcc, rc, rb (ถ้ามี), re (ถ้ามี), r1/r2 (ถ้ามี)` ≤ 0 → `MUST_BE_POSITIVE`
- `beta <= 0` → `BETA_POSITIVE`; `vbe < 0` → `VBE_NON_NEGATIVE`; `vbe >= vcc` → `VBE_BELOW_VCC`
- คืน `ModeBiasInput(mode=mode, **values)`

- [ ] **Step 5: เขียน `analyze_mode`**

- `divider`: สร้าง `BiasInput(vcc=..., r1=..., r2=..., rc=..., re=..., beta=..., vbe=...)` แล้ว `return analyze_bias(...)` (ห้ามคัดลอกสูตร Divider ใหม่)
- `fixed`: `IB=(VCC−VBE)/RB`, `IC=βIB`, `IE=(β+1)IB`, `VE=0`, `VB=VE+VBE`, `VC=VCC−IC·RC`, `VCE=VC−VE`
- `emitter`: `IB=(VCC−VBE)/(RB+(β+1)RE)`, `IC=βIB`, `IE=(β+1)IB`, `VE=IE·RE`, `VB=VE+VBE`, `VC=VCC−IC·RC`, `VCE=VC−VE`
- คืน `BiasResult(region="active", warnings=..., primary=point, independent=None, agreement_ok=None)`
- ถ้า `point.ib <= 0` หรือ `point.vce < VCE_SAT` → เพิ่ม `W_FORWARD_ACTIVE` ใน warnings
- `W_FORWARD_ACTIVE = "Forward Active model may not apply: IB ≤ 0 or VCE < 0.2 V, so the values above come from the active-region equations and are only approximate."`

- [ ] **Step 6: รันเทสต์เดิม**

```powershell
.venv\Scripts\python -m unittest discover -v
```

Expected: `OK` 40 เทสต์

- [ ] **Step 7: ตรวจค่ากับ reference อิสระ (one-off ไม่ commit)**

สร้าง `$env:TEMP\check_modes.py` ที่ import `parse_mode_inputs`, `analyze_mode` แล้ว assert ค่าต่อไปนี้ (tolerance `abs=1e-9` สำหรับ V, `abs=1e-12` สำหรับ A):

| เคส | mode | อินพุตหลัก | VB (V) | VE (V) | VC (V) | VCE (V) | IC (mA) |
|---|---|---|---|---|---|---|---|
| A1 | divider | R1=100k, R2=22k, RE=1k | 1.942157 | 1.242157 | 9.294312 | 8.052155 | 1.229858 |
| A2 | fixed | RB=1M | 0.700000 | 0.000000 | 9.514000 | 9.514000 | 1.130000 |
| A3 | emitter | RB=1M, RE=1k | 1.736603 | 1.036603 | 9.742053 | 8.705450 | 1.026340 |
| A4 | emitter | RB=1M, RE=2k | 2.599002 | 1.899002 | 9.931780 | 8.032779 | 0.940100 |

ใช้ร่วมกัน: VCC=12, RC=2.2k, β=100, VBE=0.70, หน่วย Ω ใน `raw` (หรือ kΩ ตามที่ระบุ)

Expected: ทุก assert ผ่าน

- [ ] **Step 8: Commit**

```powershell
git add bias.py
git commit -m "feat: add fixed and emitter bias calculations with per-mode inputs"
```

---

### Task 2: Mode-aware Flask UI (route, template, CSS)

**Files:**
- Modify: `app.py`
- Modify: `templates/index.html`
- Modify: `static/style.css`
- Test: `tests/test_app.py` (รันของเดิม ไม่แก้)

**Interfaces:**
- Consumes: `MODES`, `MODE_FIELDS`, `ModeBiasInput`, `parse_mode_inputs`, `analyze_mode`, `W_FORWARD_ACTIVE`, `BiasInputError`
- Produces:
  - `FIELD_DEFS: dict[str, dict]` สำหรับ 8 ช่อง (`vcc,r1,r2,rc,re,rb,beta,vbe`) มี `name,label,hint,units`
  - `MODE_LABELS: dict[str, str]` = `{"divider":"Voltage Divider Bias","fixed":"Fixed Bias","emitter":"Emitter Bias"}`
  - `DEFAULT_VALUES: dict[str, dict[str,str]]` แยกตามโหมด
  - `DEFAULT_UNITS: dict[str, str]`
  - `fields_for_mode(mode) -> tuple[dict, ...]`
  - `GET /` รองรับ `?mode=`
  - `POST /calculate` อ่าน `mode`

- [ ] **Step 1: ปรับ `app.py`**

- คง `DEFAULT_VALUES` ของ divider ไว้เหมือนเดิมทุกค่า (`"12.0"`, `"100"`, `"22"`, `"2.2"`, `"1.0"`, `"100"`, `"0.70"`)
- เพิ่มค่าเริ่มต้น:
  - fixed: `vcc="12.0"`, `rc="2.2"`, `rb="1000"`, `beta="100"`, `vbe="0.70"`
  - emitter: `vcc="12.0"`, `rc="2.2"`, `rb="1000"`, `re="1.0"`, `beta="100"`, `vbe="0.70"`
- `fields_for_mode(mode)` คืนเฉพาะช่องตาม `MODE_FIELDS[mode]` เรียงตามลำดับใน `MODE_FIELDS`
- `GET /`: อ่าน `mode = request.args.get("mode", MODE_DIVIDER)`; ถ้าไม่รู้จักให้ `mode_error="Choose a valid bias mode."` และใช้ divider form โดยไม่คำนวณ
- `POST /calculate`: อ่าน `mode = request.form.get("mode", MODE_DIVIDER)`; `parse_mode_inputs(raw, mode)` แล้ว `analyze_mode(data)`
- `region_info`: ถ้า `W_FORWARD_ACTIVE` อยู่ใน `result.warnings` คืน `{"kind":"warn","title":"Forward Active model may not apply","detail": ...}` ก่อนตรวจ region อื่น
- `render_page` ส่ง `mode`, `mode_label`, `mode_error`, `fields`, `mode_labels`, `schematic` (เฉพาะ divider; โหมดอื่น `None`)
- `extra_warnings` ยังกรอง `W_CUTOFF`, `W_SAT` เหมือนเดิม; `W_FORWARD_ACTIVE` ต้องแสดงในรายการ warnings

- [ ] **Step 2: ปรับ `templates/index.html`**

- เพิ่มฟอร์มเลือกโหมด上方ฟอร์มหลัก:
  ```html
  <form class="mode-switch" method="get" action="/">
    <label for="mode">Bias mode</label>
    <select id="mode" name="mode">...{% if mode == value %} selected{% endif %}...</select>
    <button type="submit">Load mode</button>
  </form>
  ```
- ฟอร์มหลักเพิ่ม `<input type="hidden" name="mode" value="{{ mode }}">`
- แสดง `mode_error` เป็น `<p class="error form-error">`
- schematic panel: `{% if schematic %}` แสดง SVG เดิม; `{% else %}` แสดงข้อความสั้น เช่น "Fixed Bias: RB from VCC to base, emitter grounded." / "Emitter Bias: RB from VCC to base, RE from emitter to ground."
- ผลลัพธ์เพิ่มบรรทัด `Mode: {{ mode_label }}`
- คงโครงสร้างเดิมทั้งหมดที่เทสต์เดิมอ้างถึง (`Common-Emitter Amplifier`, `Q1`, `DC Bias Results`, `Run the calculation`, `name="r1"` ฯลฯ)

- [ ] **Step 3: ปรับ `static/style.css`**

เพิ่มสไตล์ `.mode-switch` (จัดเรียงแนวนอน, ช่องไฟพอดี) และ `.form-error` โดยไม่แตะสไตล์เดิม

- [ ] **Step 4: รันเทสต์เดิม**

```powershell
.venv\Scripts\python -m unittest discover -v
```

Expected: `OK` 40 เทสต์

- [ ] **Step 5: ตรวจ route แบบ one-off (ไม่ commit)**

ใช้ Flask test client ตรวจ:
- `GET /` มี `name="mode"`, `name="r1"`, ไม่มี `name="rb"`
- `GET /?mode=fixed` มี `name="rb"`, ไม่มี `name="r1"`/`name="r2"`
- `GET /?mode=emitter` มี `name="rb"` และ `name="re"`, ไม่มี `name="r1"`
- `POST /calculate` (ไม่มี `mode`) → มี `VB`/`IC` ของ Divider A1
- `POST mode=fixed` A2 → มี `1.13` (mA) และ `9.51` (V)
- `POST mode=emitter` A3 → มี `1.03` (mA) และ `8.71` (V)
- `POST mode=emitter` A4 (RE=2k) → มี `0.94` (mA) และ `8.03` (V)
- `POST mode=hfe` → มี `Choose a valid bias mode.` และไม่มีตารางผล
- `POST mode=fixed` `rb=0` → มี `Must be greater than 0.` และไม่มีตารางผล

Expected: ทุกข้อเป็นจริง

- [ ] **Step 6: Commit**

```powershell
git add app.py templates/index.html static/style.css
git commit -m "feat: let the Flask form choose and render three bias modes"
```

---

### Task 3: Independent reference + `docs/validation.md`

**Files:**
- Create: `docs/validation.md`

**Interfaces:**
- Consumes: ค่าอ้างอิงจาก Task 1 Step 7 (คำนวณตรงจากสูตร ไม่ import `bias.py`)
- Produces: ตาราง A1–A5 ที่มีอินพุต, ค่าคาดหมาย, ช่องผลจริง/วิธีตรวจ/สถานะ/หลักฐาน (เว้นว่างไว้ก่อน)

- [ ] **Step 1: เขียน `docs/validation.md`**

ต้องมี:
- หัวข้อ วิธีและเกณฑ์: VCC=12, RC=2.2k, β=100, VBE=0.70, tolerance `IC ≤ 0.01 mA`, `VCE ≤ 0.02 V`, เทียบกับค่าอ้างอิงที่ไม่ปัดเศษ
- สมการที่ใช้คำนวณมือ (Fixed/Emitter/Divider)
- ตาราง A1–A5 คอลัมน์: `กรณี | โหมดและอินพุต | ค่าคาดหมาย | ผลที่เห็น | วิธีตรวจ | สถานะ | หลักฐาน`
- เติมค่าคาดหมายจากตาราง Task 1 Step 7; A5 เขียนว่า "error ที่ RB, ไม่มีผลลัพธ์ค้าง"
- ระบุว่าค่าอ้างอิงคำนวณก่อนเปิดเว็บและไม่ได้มาจากโปรแกรมที่กำลังตรวจ

- [ ] **Step 2: ตรวจความสอดคล้องของตัวเลข**

เทียบค่าที่เขียนในตารางกับ `$env:TEMP\ref_calc.py` (หรือคำนวณซ้ำด้วยสูตรตรง) — ต้องตรงทุกค่า

- [ ] **Step 3: Commit**

```powershell
git add docs/validation.md docs/superpowers/specs/2026-11-17-bjt-bias-modes-design.md docs/superpowers/plans/2026-11-17-bjt-bias-modes.md
git commit -m "docs: add Lab 03 design, plan, and A1-A5 validation table"
```

---

### Task 4: Browser acceptance A1–A5

**Files:**
- Modify: `docs/validation.md`

**Interfaces:**
- Consumes: ตาราง A1–A5 จาก Task 3, แอปที่รันบน `http://127.0.0.1:5000`
- Produces: ตารางที่กรอกผลจริง วิธีตรวจ และสถานะ `PASS`/`FAIL`/`NOT RUN` พร้อมหลักฐานอย่างน้อยหนึ่งกรณี

- [ ] **Step 1: เริ่ม Flask server**

```powershell
$server = Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "app.py" -PassThru
Start-Sleep -Seconds 3
Invoke-WebRequest http://127.0.0.1:5000 -UseBasicParsing | Select-Object StatusCode
```

Expected: `200`

- [ ] **Step 2: เปิดเว็บด้วย browser tool**

ใช้ OpenCode Browser (`browser_navigate` + `browser_snapshot`) เป็นหลัก เพราะ Playwright MCP ต้อง restart OpenCode เพื่อโหลด config — บันทึกวิธีจริงว่า `OpenCode Browser` และระบุเหตุผลว่า Playwright MCP ไม่ได้โหลดในเซสชันนี้ (ใบงานอนุญาตให้ใช้วิธีสำรอง)

- [ ] **Step 3: รัน A1–A5 ทีละกรณี**

สำหรับแต่ละกรณี: เลือกโหมด → กรอกช่องตามหน่วยบนฟอร์ม → กด Calculate → อ่าน Snapshot หลังส่งฟอร์ม → เทียบค่าคาดหมาย → บันทึก `ผลที่เห็น`, `วิธีตรวจ`, `สถานะ` และหลักฐาน (ข้อความผลหรือ screenshot)

- A1: Divider, R1=100k, R2=22k, RE=1k
- A2: Fixed, RB=1,000 kΩ (=1 MΩ)
- A3: Emitter, RB=1,000 kΩ, RE=1 kΩ
- A4: Emitter, RB=1,000 kΩ, RE=2 kΩ — ยืนยันว่าโหมดยังเป็น Emitter และค่าอื่นเท่า A3
- A5: Fixed, RB=0 → ต้องเห็น error และไม่มีผลรอบก่อน

- [ ] **Step 4: เก็บหลักฐาน**

บันทึกข้อความผลจาก Snapshot อย่างน้อยหนึ่งกรณี และถ้า `browser_take_screenshot` ใช้ได้ให้บันทึกไฟล์/คำอธิบายไว้ในช่องหลักฐาน

- [ ] **Step 5: หยุด server และ commit**

```powershell
Stop-Process -Id $server.Id
git add docs/validation.md
git commit -m "docs: record browser acceptance results for A1-A5"
```

---

### Task 5: README, full verification, push

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: ทุกอย่างจาก Task 1–4
- Produces: README ที่อธิบายสามโหมด, วิธีรัน, วิธีรันเทสต์, วิธีตรวจผ่าน Browser; commit ที่ push ขึ้น `origin/main`

- [ ] **Step 1: อัปเดต README**

เพิ่มหัวข้อ Lab 03:
- สามโหมดและฟิลด์ที่ใช้
- วิธีรัน (คงคำสั่งเดิม)
- วิธีรันเทสต์เดิม
- วิธีตรวจ A1–A5 และลิงก์ `docs/validation.md`
- ระบุว่าไม่เพิ่ม unittest ใหม่ เพราะใบงานกำหนดให้ตรวจผ่าน Browser

- [ ] **Step 2: รันเทสต์ทั้งหมดอีกครั้ง**

```powershell
.venv\Scripts\python -m unittest discover -v
```

Expected: `OK` 40 เทสต์

- [ ] **Step 3: ตรวจ diff ก่อน commit**

```powershell
git diff
git status --short
```

Expected: เปลี่ยนเฉพาะไฟล์งาน Lab 03; ไม่มี `.venv`, `.env`, credentials

- [ ] **Step 4: Commit และ push**

```powershell
git add README.md
git commit -m "docs: document the three bias modes and browser acceptance"
git push origin main
git status -sb
git rev-parse HEAD
git rev-parse origin/main
```

Expected: `## main...origin/main` ไม่มี ahead/behind และ SHA ของ HEAD ตรงกับ `origin/main`

- [ ] **Step 5: รายงานผล**

รายงาน GitHub URL, Commit SHA, ตาราง A1–A5 โดยสรุป, วิธีตรวจจริง, และไฟล์ที่เปลี่ยน

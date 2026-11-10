# BJT Common-Emitter DC Bias — Design

วันที่: 2026-11-10
รายวิชา: ENG29 2121
สถานะ: รออนุมัติ

## ทำไมทำ (intent)

นักศึกษาต้องส่งงาน lab ที่เป็น **เว็บแอป Flask จริง** ไม่ใช่สคริปต์ command line
เพื่อคำนวณจุดทำงาน DC ของวงจรไบอัสแบบ voltage divider (Common-Emitter)
และต้อง **เทียบผลกับการคำนวณทางวิศวกรรมที่เป็นอิสระจากกัน** เพื่อยืนยันว่าสูตรที่ใช้ถูก
ภายในวันนี้ต้องรันบน localhost ได้และ commit ขึ้น GitHub

## เป้าหมาย

1. กรอก `VCC, R1, R2, RC, RE, beta, VBE` แล้วเห็นจุดทำงาน DC พร้อมหน่วย
2. คำนวณสองวิธีอิสระต่อกัน และแสดงผลเทียบกันบนหน้าเว็บพร้อมผลต่าง
3. ตรวจสอบ input และเตือนโหมดการทำงาน (cutoff / active / saturation)
4. แยกส่วนวิศวกรรม / route / template / CSS / test ออกจากกันชัดเจน
5. `python -m unittest -v` ผ่านทั้งหมด และรัน `python app.py` ขึ้น localhost:5000 ได้
6. commit + push ขึ้น GitHub repo เดิม (public)

## สิ่งที่ไม่ทำ (non-goals)

- AC analysis, transient, frequency response
- circuit editor / วาด schematic แบบลากวาง
- FET / MOSFET / op-amp
- JSON API, JavaScript framework, build step, database, auth, deployment
- ลบหรือแก้ `electrical.py` และเทสต์เดิม (งาน lab คนละชิ้น)
- ทำความสะอาดไฟล์ขยะใน repo (`git-evidence.txt`, `reflection.txt`,
  ไฟล์ชื่อเสีย) — แยกเป็นงานต่างหาก

## anti-goals (ถ้าเป็นแบบนี้ถือว่าล้มเหลว)

- หน้าเว็บโชว์ผลได้ แต่ตัวเลขไม่ตรงกับที่คิดมือ
- "การเทียบผล" เป็นเพียงคอมเมนต์หรือค่าคงที่ในเทสต์ มองไม่เห็นตอนเดโม
- logic วิศวกรรมไปฝังอยู่ใน route หรือ template
- ต้องติดตั้งของนอกเหนือจาก Flask เพื่อให้เดโมรันได้
- ใช้เวลาเกินวันนี้เพราะพยายามทำมากกว่าที่กำหนด

## ทางเลือกที่พิจารณา

| ทางเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| **A. คำนวณสองวิธีในโค้ด โชว์เทียบกัน (เลือก)** | เห็นการตรวจสอบได้ตอนเดโม, จับ error พีชคณิตได้จริง, มีของให้แคปส่ง lab | เพิ่มโค้ด ~40 บรรทัด และตารางสองคอลัมน์ |
| B. ค่าอ้างอิงจากใบ lab ใส่ในเทสต์อย่างเดียว | น้อยที่สุด | "independent calculation" มองไม่เห็นในเดโม พิสูจน์ได้จุดเดียว |
| C. เรียก library ภายนอก (เช่น PySpice) | แม่นกว่า | ต้องติดตั้งของหนัก ผิดข้อจำกัดเวลาและ anti-goal |

เลือก **A** เพราะทำให้การเทียบผลเป็น deliverable จริง

## การตัดสินใจที่ตกลงแล้ว

### 1. วิธีคำนวณหลัก — Thevenin equivalent

```
VBB = VCC * R2 / (R1 + R2)
RB  = R1 * R2 / (R1 + R2)
IB  = (VBB - VBE) / (RB + (beta + 1) * RE)
IC  = beta * IB
IE  = (beta + 1) * IB
VE  = IE * RE
VB  = VBE + VE
VC  = VCC - IC * RC
VCE = VC - VE
```

### 2. วิธีอิสระ — nodal analysis (ไม่ผ่าน VBB/RB เลย)

```
VE' = (VCC/R1 - VBE*(1/R1 + 1/R2)) / (1/R1 + 1/R2 + 1/((beta+1)*RE))
IE' = VE' / RE
IB' = IE' / (beta + 1)
IC' = beta * IB'
VB' = VE' + VBE
VC' = VCC - IC' * RC
VCE' = VC' - VE'
```

ทั้งสองวิธีเป็นพีชคณิตคนละเส้นทาง จึงใช้ตรวจจับกันได้
เกณฑ์ตรงกัน: `math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)`
ถ้าไม่ตรง → ถือเป็น internal error แสดงแบนเนอร์เตือน (ไม่ควรเกิด)

**ข้อยกเว้น:** การเทียบผลใช้ได้เฉพาะโหมด active/saturation เท่านั้น
(ในโหมด cutoff สูตร nodal ให้กระแสติดลบซึ่งไม่มีความหมายทางกายภาพ)
ลำดับการทำงานจึงเป็น: validate → ตรวจโหมด → ถ้า cutoff ให้ clamp ค่าและ
**ไม่แสดงตารางเทียบ/ไม่ขึ้นแบนเนอร์** แต่แสดงหมายเหตุ "ไม่เทียบผล: วงจรอยู่ในโหมด cutoff"
เทสต์ agreement จึงไล่เฉพาะจุดที่อยู่ใน active/saturation

### 3. กติกาโหมดการทำงาน (ตามลำดับ)

1. **cutoff** เมื่อ `VBB <= VBE` (กระแส base เป็นลบ/ศูนย์)
   → รายงาน `IB = IC = IE = 0`, `VE = 0`, `VC = VCC`, `VCE = VCC`
2. **saturation** เมื่อ `VCE < VCE_SAT` (`VCE_SAT = 0.2 V`)
   → รายงานค่าที่คำนวณได้ตามสูตร active (ไม่ clamp) พร้อมเตือนว่า
   สมมติฐาน active region ใช้ไม่ได้ ผลที่เห็นเป็นค่าประมาณ
3. **active** กรณีอื่น

### 4. คำเตือนเพิ่มเติม (1 ข้อ)

- **divider ไม่แข็ง** เมื่อกระแสในตัวแบ่ง `VCC/(R1+R2) < 10 * IB`
  → เตือนว่าจุดทำงานจะไวต่อ beta (กฎ 10 เท่า)

### 5. Validation

- ทุกช่องต้องเป็นตัวเลข finite; ว่างหรือแปลงไม่ได้ → error
- `VCC > 0`, `R1 > 0`, `R2 > 0`, `RC > 0`, `RE > 0`
- `beta > 0`, `VBE >= 0`, `VBE < VCC`
- ผิดหลายข้อ → แสดงทุกข้อพร้อมกัน ไม่หยุดที่ข้อแรก

### 6. หน่วยและการแสดงผล

| ค่า | หน่วย |
|---|---|
| VB, VE, VC, VCE | V |
| IB | µA |
| IC, IE | mA |
| beta | ไม่มีหน่วย |

ปัดเศษ 4 significant figures (สไตล์เดียวกับ `electrical.py` ที่ใช้ `:.4g`)

### 7. โครงสร้างไฟล์

```
app.py                     # Flask app + routes (ไม่มีสูตรวิศวกรรม)
bias.py                    # validate + thevenin + nodal + region + warnings
templates/index.html       # ฟอร์ม + ตารางผล + คำเตือน
static/style.css           # ไฟล์เดียว ไม่มี framework
tests/test_bias.py         # เทสต์ logic: ค่าจริง, cutoff, saturation, validation, agreement
tests/test_app.py          # เทสต์ route ด้วย Flask test client
requirements.txt           # Flask
README.md                  # แก้ conflict marker + วิธีรัน
```

### 8. Route

- `GET /` → ฟอร์ม
- `POST /calculate` → validate + คำนวณ + render หน้าเดิม
  - input ผิด → HTTP 200 พร้อม error ใต้ช่องนั้น และคงค่าที่กรอกไว้
  - สำเร็จ → ตารางผลสองคอลัมน์ (Thevenin / Nodal) + ผลต่าง + โหมด + คำเตือน

ไม่มี endpoint อื่น ไม่มี JavaScript

### 9. เทสต์ (unittest — ตามสไตล์ repo เดิม ไม่เพิ่ม dependency)

- เคสค่ามาตรฐาน 1 เคส ที่คิดมือไว้ล่วงหน้า
- cutoff 1 เคส, saturation 1 เคส
- validation: 0, ค่าลบ, NaN/inf, ไม่ใช่ตัวเลข, beta <= 0, VBE >= VCC
- agreement: ไล่ค่าหลายชุดแล้วยืนยันสองวิธีตรงกัน
- route: GET 200 มีฟอร์ม, POST ถูกต้องเห็นตัวเลข, POST ผิดเห็น error

### 10. การรันและส่งงาน

- venv ที่ `.venv` (อยู่ใน `.gitignore` แล้ว) + `pip install -r requirements.txt`
- `python app.py` → http://127.0.0.1:5000
- commit message บอกขอบเขตงาน, push ขึ้น `origin/main`
- ขอบเขตที่ commit: ไฟล์งาน lab (`app.py`, `bias.py`, `templates/`, `static/`,
  `tests/`, `requirements.txt`, `README.md`) **รวม** `docs/superpowers/specs/`
  ตามธรรมเนียมของ workflow นี้ — ไม่แตะไฟล์ lab เดิมหรือไฟล์ขยะ
- push ได้เลยเมื่อเทสต์ผ่าน ไม่ต้องหยุดรออนุมัติรอบสอง (เจ้าของงานสั่งไว้แล้ว)

### 11. README

เก็บเนื้อหาทั้งสองฝั่งของ conflict ไว้ ไม่ลบข้อความเดิม:

1. `# gitlab` + "ใช้สำหรับเรียนแลปคอมโปรไฟฟ้า" (จาก HEAD)
2. `DC Circuit Calculator` + คำอธิบายวัตถุประสงค์ภาษาไทย (จาก 42fcee8)
3. เพิ่มหัวข้อใหม่ "BJT Common-Emitter DC Bias (ENG29 2121)" พร้อมวิธีติดตั้ง รัน และรันเทสต์

## ข้อจำกัด

- ต้องเสร็จวันนี้ (2026-11-10)
- Python 3.10.11, ยังไม่มี Flask ในเครื่อง
- repo เป็น public — ไฟล์ที่ commit จะมองเห็นได้ทันที

## สิ่งที่เหลือให้ผู้สร้างตัดสินใจเอง

- หน้าตา HTML/CSS, label, การจัดวางตาราง
- ตัวเลขเคสทดสอบจริง (คำนวณตอนเขียนเทสต์)
- ถ้อยคำของ commit message
- จะใส่ `Pd = VCE * IC` เพิ่มหรือไม่ (ไม่บังคับ)

# BJT DC Bias — Three Modes (Lab 03) — Design

วันที่: 2026-11-17
รายวิชา: ENG29 2121
สถานะ: อนุมัติแล้ว (แนวทาง A)

## ทำไมทำ (intent)

ต่อยอดเว็บ Flask จาก Lab 2 ให้เลือกวงจรไบอัสได้สามแบบ — Voltage Divider (ของเดิม),
Fixed Bias และ Emitter Bias แบบแหล่งจ่ายเดียว — แล้วตรวจผลบนหน้าเว็บจริงผ่าน
Browser โดยใช้ตาราง A1–A5 ของนักศึกษา คงผลของ Divider เดิมไว้ทุกกรณี

## เป้าหมาย

1. เลือกโหมด `divider` / `fixed` / `emitter` ได้จากหน้าเว็บ
2. ฟอร์มแสดงเฉพาะช่องที่โหมดนั้นต้องใช้ และโหลดฟอร์มใหม่เมื่อเปลี่ยนโหมด (ไม่ใช้ JS)
3. `bias.py` มีฟังก์ชันแยกสำหรับ Fixed และ Emitter ตามสมการในใบงาน
4. validation ตรวจเฉพาะช่องที่โหมดใช้, เก็บ error หลายช่อง, โหมดไม่รู้จักแจ้ง error
5. Divider ให้ผลเหมือน Lab 2 ทุกกรณี (A1) และเทสต์เดิมทั้ง 40 ตัวยังผ่าน
6. เตือนเมื่อแบบจำลอง Forward Active อาจใช้ไม่ได้ (`IB ≤ 0` หรือ `VCE < 0.2 V`)
7. ตรวจ A1–A5 ผ่าน Browser จริง, บันทึก `docs/validation.md` พร้อมหลักฐาน
8. อัปเดต README, commit และ push ขึ้น GitHub

## สิ่งที่ไม่ทำ (non-goals)

- SPICE, DC Load Line, AC/Transient, bypass capacitor
- unittest ใหม่ (ใบงานกำหนดให้ตรวจผ่าน Browser)
- JSON API, JavaScript framework, build step, database, auth
- แก้ `electrical.py` / `test_electrical.py`
- ทำความสะอาดไฟล์ขยะใน repo (`git-evidence.txt`, `reflection.txt`, ไฟล์ชื่อเสีย)

## anti-goals

- Divider ให้ผลเปลี่ยนจาก Lab 2 หรือเทสต์เดิมพัง
- สมการวิศวกรรมไปอยู่ใน route/template
- โหมดไม่รู้จักถูกตีความเป็น Divider เงียบ ๆ
- แสดงผลรอบก่อนเป็นผลของอินพุตใหม่ที่กรอกผิด
- เพิ่ม dependency นอกเหนือจาก Flask

## ทางเลือกที่พิจารณา

| ทางเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| **A. ต่อยอด `bias.py` เดิม (เลือก)** | Divider คงเดิมทุกบรรทัด, เทสต์เดิมผ่าน, ใช้ `OperatingPoint` เดิม | ไฟล์ `bias.py` ยาวขึ้น |
| B. แยก `dc_bias.py` ใหม่ ใช้คีย์ `vb_v/ic_ma` | ชื่อคีย์ตรงใบงานกว่า | เสี่ยงทำ Divider/เทสต์เดิมพัง, ต้องแก้ app/template ทั้งชุด |
| C. ทำเว็บใหม่ | สะอาด | ใบงานห้าม |

เลือก **A** เพราะ A1 บังคับให้ Divider ต้องเหมือนเดิม และใบงานอนุญาตไฟล์ที่ทำหน้าที่เดียวกัน

## การตัดสินใจ

### 1. ไฟล์และโครงสร้าง

- `bias.py` — เพิ่ม `rb`, `ModeBiasInput`, `parse_mode_inputs`, `analyze_mode`
  โดย **ไม่แก้** `parse_inputs`, `_thevenin`, `_nodal`, `analyze_bias` เดิม
- `app.py` — อ่าน `mode`, เลือกช่อง/ฟังก์ชันตามโหมด, คง route `GET /`, `POST /calculate`
- `templates/index.html` — mode selector + ฟิลด์ตามโหมด + แสดงโหมดในผล
- `static/style.css` — เพิ่มสไตล์ mode switch
- `docs/validation.md` — ตาราง A1–A5 + ค่าอ้างอิงอิสระ
- `tests/` — ไม่แก้และไม่เพิ่ม

### 2. โหมดและฟิลด์

| โหมด | ฟิลด์ที่ต้องใช้ | ฟิลด์ที่ไม่ต้องใช้ |
|---|---|---|
| `divider` | vcc, r1, r2, rc, re, beta, vbe | rb |
| `fixed` | vcc, rb, rc, beta, vbe | r1, r2, re |
| `emitter` | vcc, rb, rc, re, beta, vbe | r1, r2 |

- ค่าเริ่มต้น `mode = "divider"` เพื่อให้ POST เดิมและเทสต์เดิมทำงานเหมือนเดิม
- โหมดไม่รู้จัก → error ระดับฟอร์ม ไม่คำนวณ ไม่เดาเป็น Divider

### 3. Validation

- ใช้กติกาเดิม: ว่าง → required, ไม่ใช่ตัวเลข → number, ไม่ finite → finite
- ตรวจค่าบวกเฉพาะช่องที่โหมดใช้ และ `beta > 0`, `0 ≤ vbe < vcc`
- เก็บ error ทุกช่องพร้อมกัน

### 4. สมการ (SI: V, A, Ω)

```
Fixed   : IB = (VCC - VBE) / RB
Emitter : IB = (VCC - VBE) / (RB + (beta + 1) * RE)
Divider : IB = (VTH - VBE) / (RTH + (beta + 1) * RE)   [ของเดิม]
IC = beta * IB
IE = (beta + 1) * IB
VE = 0 (Fixed) หรือ IE * RE (Emitter/Divider)
VB = VE + VBE
VC = VCC - IC * RC
VCE = VC - VE
```

- Fixed/Emitter คืน `OperatingPoint` และ `BiasResult(independent=None, agreement_ok=None)`
- Divider เรียก `analyze_bias` เดิมทั้งหมด (Thevenin + nodal + region)

### 5. คำเตือนแบบจำลอง

- ค่าคงที่ใหม่ `W_FORWARD_ACTIVE` แจ้งว่า `IB ≤ 0` หรือ `VCE < 0.2 V`
  ทำให้แบบจำลอง Forward Active อาจใช้ไม่ได้ และค่าที่เห็นมาจากสมการ active
- ไม่คำนวณค่าที่ถูกต้องของ cutoff/saturation
- Divider ยังใช้ region banner เดิม (cutoff/saturation) ไม่เปลี่ยน

### 6. UI

- `GET /?mode=fixed` เรนเดอร์ฟอร์มของโหมดนั้น
- ตัวเลือกโหมดเป็น `<form method="get">` + `<select name="mode">` + ปุ่ม "Load mode"
  (ไม่ใช้ JavaScript)
- ฟอร์มหลัก POST ไป `/calculate` พร้อม hidden `mode`
- ผลลัพธ์ระบุชื่อโหมด; error คงค่าและโหมดที่กรอก
- schematic เดิมแสดงเฉพาะ divider; โหมดใหม่แสดงคำอธิบายวงจรสั้น ๆ

### 7. การตรวจสอบ

- รันเทสต์เดิม `.venv\Scripts\python -m unittest discover -v` ต้องผ่านทั้ง 40 ตัว
- คำนวณค่าอ้างอิงอิสระด้วยสูตรตรง ๆ (ไม่ import `bias.py`) แล้วบันทึกก่อนเปิดเว็บ
- ตรวจ A1–A5 ผ่าน Browser (Playwright MCP ก่อน; ถ้าไม่พร้อมใช้ OpenCode Browser
  และระบุวิธีจริง), เก็บหลักฐานอย่างน้อยหนึ่งกรณี
- อัปเดต README + commit + push

## ข้อจำกัด

- Windows, PowerShell; venv ยังไม่มี (Python 3.12.7)
- dependency เดียว: Flask
- ต้องคงพฤติกรรม Divider และเทสต์เดิมทุกตัว

## สิ่งที่เหลือให้ผู้สร้างตัดสินใจ

- ถ้อยคำรายละเอียดใน UI และ README
- รูปแบบตาราง `docs/validation.md`
- จะแสดง schematic ของโหมดใหม่อย่างไร (ข้อความสั้นหรือ SVG)

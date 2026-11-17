# Lab 03 — Browser Acceptance A1–A5

## เกณฑ์ที่ใช้ร่วมกัน

- V<sub>CC</sub> = 12 V, R<sub>C</sub> = 2.2 kΩ, β = 100, V<sub>BE</sub> = 0.70 V
- tolerance: I<sub>C</sub> ต่างไม่เกิน 0.01 mA, V<sub>CE</sub> ต่างไม่เกิน 0.02 V
- เทียบกับค่าอ้างอิงที่ยังไม่ปัดเศษ (ตารางด้านล่าง)
- วิธีตรวจจริงจะระบุเป็น `Playwright MCP`, `OpenCode Browser` หรือ `Manual`

## ค่าอ้างอิงอิสระ (คำนวณก่อนเปิดเว็บ)

ค่าต่อไปนี้คำนวณตรงจากสมการในใบงานด้วยเครื่องคิดเลข/สคริปต์แยก
โดยไม่ import โมดูล `bias.py` ของโปรแกรมที่กำลังตรวจ

```
Fixed   : IB = (VCC − VBE) / RB
Emitter : IB = (VCC − VBE) / [RB + (β + 1)RE]
Divider : IB = (VTH − VBE) / [RTH + (β + 1)RE]
          VTH = VCC·R2/(R1+R2), RTH = R1R2/(R1+R2)
IC = βIB, IE = (β+1)IB
VE = 0 (Fixed) หรือ IE·RE (Emitter/Divider)
VB = VE + VBE, VC = VCC − IC·RC, VCE = VC − VE
```

| เคส | โหมด | อินพุต | V<sub>B</sub> (V) | V<sub>E</sub> (V) | V<sub>C</sub> (V) | V<sub>CE</sub> (V) | I<sub>C</sub> (mA) |
|---|---|---|---|---|---|---|---|
| A1 | Divider | R1=100 kΩ, R2=22 kΩ, RE=1 kΩ | 1.942157 | 1.242157 | 9.294312 | 8.052155 | 1.229858 |
| A2 | Fixed | RB=1 MΩ | 0.700000 | 0.000000 | 9.514000 | 9.514000 | 1.130000 |
| A3 | Emitter | RB=1 MΩ, RE=1 kΩ | 1.736603 | 1.036603 | 9.742053 | 8.705450 | 1.026340 |
| A4 | Emitter | RB=1 MΩ, RE=2 kΩ | 2.599002 | 1.899002 | 9.931780 | 8.032779 | 0.940100 |
| A5 | Fixed | RB=0 | — | — | — | — | — |

**A1 baseline ก่อนแก้ (Lab 2):** VB 1.94 V, VE 1.24 V, VC 9.29 V, VCE 8.05 V,
IB 12.3 µA, IC 1.23 mA, IE 1.24 mA — ตรงกับค่าอ้างอิง A1

**A4 prediction:** เมื่อเพิ่ม RE จาก 1 kΩ เป็น 2 kΩ ที่ RB คงที่
กระแสฐานและกระแสสะสมควร **ลดลง** (I<sub>C</sub> จาก ~1.026 เป็น ~0.940 mA)
เพราะ RE ต่อต้านกระแสอิมิตเตอร์มากขึ้น

## ตารางบันทึกผลจริง

| กรณี | เลือกโหมดและกรอกค่า | คาดหมายก่อนรัน | ผลที่เห็น | วิธีตรวจ | สถานะ | หลักฐาน |
|---|---|---|---|---|---|---|
| A1 · โหมดเดิม | Divider · R1=100 kΩ, R2=22 kΩ, RE=1 kΩ | IC 1.229858 mA · VCE 8.052155 V และตรงกับ Lab 2 | Mode: Voltage Divider Bias · VB 1.94 V · VE 1.24 V · VC 9.29 V · VCE 8.05 V · IB 12.3 µA · IC 1.23 mA · IE 1.24 mA | OpenCode Browser | PASS | Snapshot ของ `/calculate` ตรงกับ baseline Lab 2 ทุกค่า |
| A2 · Fixed | Fixed · RB=1 MΩ (ฟอร์มไม่มีช่อง R1/R2/RE) | IC 1.130000 mA · VCE 9.514000 V (ไม่ต้องกรอก RE) | Mode: Fixed Bias · VB 0.70 V · VE 0.00 V · VC 9.51 V · VCE 9.51 V · IB 11.3 µA · IC 1.13 mA · IE 1.14 mA | OpenCode Browser | PASS | Snapshot หลังส่งฟอร์ม + ค่า `rb=1 MΩ` ในฟอร์มที่คงอยู่ |
| A3 · Emitter | Emitter · RB=1 MΩ, RE=1 kΩ | IC 1.026340 mA · VCE 8.705450 V | Mode: Emitter Bias · VB 1.74 V · VE 1.04 V · VC 9.74 V · VCE 8.71 V · IB 10.3 µA · IC 1.03 mA · IE 1.04 mA | OpenCode Browser | PASS | Snapshot หลังส่งฟอร์ม |
| A4 · เปลี่ยนค่าเดียว | Emitter · เหมือน A3 แต่ RE=2 kΩ | IC ลดจาก A3 → 0.940100 mA · VCE 8.032779 V | Mode: Emitter Bias (คงเดิม) · VB 2.60 V · VE 1.90 V · VC 9.93 V · VCE 8.03 V · IB 9.4 µA · IC 0.94 mA · IE 0.95 mA | OpenCode Browser | PASS | `docs/images/lab03-a4-emitter.png` |
| A5 · อินพุตผิด | Fixed · RB=0 | มีข้อความให้แก้ RB, เว็บไม่ล่ม, ไม่มีผลรอบก่อน | ใต้ช่อง RB ขึ้น `Must be greater than 0.` · ไม่มีตารางผล · ไม่มี `Mode:` ค้างจากรอบก่อน · โหมดยังเป็น Fixed Bias และ RB=0 ยังอยู่ในฟอร์ม | OpenCode Browser | PASS | `docs/images/lab03-a5-rb-error.png` |

### หมายเหตุวิธีตรวจ

Playwright MCP ยังไม่ถูกโหลดในเซสชันนี้ (ต้อง restart OpenCode เพื่ออ่าน config) จึงใช้
**OpenCode Browser** ซึ่งเป็นวิธีสำรองที่ใบงานอนุญาต — เปิด `http://127.0.0.1:5000`
กรอกฟอร์มจริง กดปุ่ม Calculate จริง แล้วอ่านผลจาก accessibility snapshot และ screenshot
ของหน้าเว็บ ไม่ได้ยิง HTTP ตรงหรือเรียกฟังก์ชัน Python

### ตรวจเพิ่ม: คำเตือน Forward Active

นอกเหนือจาก A1–A5 ตรวจกรณีที่แบบจำลอง Forward Active อาจใช้ไม่ได้ —
Fixed Bias, RB=1 MΩ, RC=22 kΩ (กระแสสะสมสูงจน VCE ติดลบ)

- ผลที่เห็น: VC −12.86 V · VCE −12.86 V และขึ้นคำเตือน
  “Forward Active model may not apply … IB ≤ 0 or VCE < 0.2 V” หนึ่งครั้ง พร้อมค่า IB/VCE
- สถานะ: PASS (OpenCode Browser)

### ตรวจเพิ่ม: schematic ของแต่ละโหมด

เดิมโหมด Fixed/Emitter แสดงเพียงข้อความสั้น จึงเพิ่ม SVG ของแต่ละโหมด
และตรวจในเบราว์เซอร์ว่ารูปตรงกับวงจรและค่าที่กรอก

| โหมด | สิ่งที่เห็นบนรูป | สถานะ |
|---|---|---|
| Divider | R1, R2, RC, RE + ค่าที่กรอก | PASS |
| Fixed | RB จาก VCC ลงเบส, RC ลงคอลเลกเตอร์, อีมิตเตอร์ลงกราวด์ตรง (ไม่มี R2/RE) | PASS |
| Emitter | RB จาก VCC ลงเบส, RC ลงคอลเลกเตอร์, RE จากอีมิตเตอร์ลงกราวด์ (ไม่มี R2) | PASS |

- ค่าบนรูปเปลี่ยนตามที่กรอก เช่น RB 1 MΩ และ RE 2 kΩ ใน A4
- หน้า error (RB=0) ยังแสดงรูปของโหมด Fixed
- screenshot ที่อัปเดตแล้ว: `docs/images/lab03-a4-emitter.png`, `docs/images/lab03-a5-rb-error.png`

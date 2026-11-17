# Bias Schematics for All Three Modes — Plan

**Goal:** ให้โหมด Fixed และ Emitter มี schematic ของตัวเองแทนข้อความสั้น โดยไม่แตะสูตรหรือผลลัพธ์

**Architecture:** `app.py` ส่ง label ของทุกช่องที่โหมดใช้ (รวม `rb`) ให้ template เสมอ `templates/index.html` เลือก SVG ตาม `mode` สามบล็อกแยกกัน โดยคง SVG divider เดิมไว้ทั้งหมด

**Spec:** `docs/superpowers/specs/2026-11-17-bjt-bias-schematics-design.md`

## Global Constraints

- ไม่เพิ่ม dependency, ไม่ใช้ JavaScript, ไม่แตะ `bias.py` / `tests/`
- SVG divider เดิมต้องไม่เปลี่ยน
- เทสต์เดิม 49 ตัวต้องผ่าน

### Task 1: ส่ง label ครบทุกช่อง และวาด SVG สองโหมด

**Files:**
- Modify: `app.py`, `templates/index.html`, `static/style.css`

- [ ] **Step 1: `schematic_labels` รองรับ `rb`** — วนจากคีย์ของ `values` ไม่ใช่ `FIELDS`
- [ ] **Step 2: `render_page` ส่ง `schematic` ทุกโหมด** (ลบเงื่อนไข `if mode == MODE_DIVIDER`)
- [ ] **Step 3: template แยกสาม SVG** — divider เดิม / fixed / emitter พร้อม `aria-label` และ `<title>` ของตัวเอง
- [ ] **Step 4: ลบ `.schematic-note`** ออกจาก template และ CSS
- [ ] **Step 5: ตรวจ route (one-off, ไม่ commit)** — ทั้งสามโหมดมี `class="schematic"` ไม่มี `schematic-note`; fixed/emitter แสดงค่า RB ที่กรอก
- [ ] **Step 6: รันเทสต์เดิม** — `.venv\Scripts\python -m unittest discover -v` → 49 OK
- [ ] **Step 7: ตรวจเบราว์เซอร์** — ทั้งสามโหมดเห็นรูป, ค่าบนรูปตรงกับฟอร์ม, retake screenshot A4/A5
- [ ] **Step 8: Commit**

### Task 2: อัปเดตเอกสารและตรวจรอบสุดท้าย

- [ ] **Step 1: README** — ระบุว่าทุกโหมดมี schematic
- [ ] **Step 2: `docs/validation.md`** — บันทึกผลตรวจรูปทั้งสามโหมด
- [ ] **Step 3: เทสต์ + commit**

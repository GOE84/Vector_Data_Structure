# 📚 AI Tutor: Vector Data Structure API

โปรเจกต์นี้เป็นระบบ **REST API** สำหรับจำลองครูผู้ช่วยสอน (AI Tutor) ที่จะช่วยให้คำใบ้และตรวจวิเคราะห์โค้ดเรื่อง **"Vector (Dynamic Array)"** สำหรับนักศึกษา

## ⚙️ 1. สิ่งที่ต้องติดตั้ง (Prerequisites)

ก่อนเริ่มใช้งานระบบนี้ คุณจะต้องติดตั้งโปรแกรมเหล่านี้ในเครื่องก่อน:
1. **[Python 3.9+](https://www.python.org/downloads/)**
2. **[Ollama](https://ollama.com/)** (ใช้เพื่อจำลองโมเดล AI ให้อยู่ในเครื่องของเรา)

---

## 📥 2. โหลดโมเดล AI (ทำแค่ครั้งแรกครั้งเดียว)

เปิด Terminal และรัน 2 คำสั่งนี้เพื่อก๊อปปี้สมองของ AI มาไว้ในเครื่อง:
```bash
ollama run gemma3:12b
ollama run nomic-embed-text
```
*(ตอนที่รัน `nomic-embed-text` ถ้ามันขึ้น Error ว่า require input text ไม่ต้องตกใจครับ ถือว่าโหลดสำเร็จแล้ว ให้กด `/bye` ออกจากแชทได้เลย)*

---

## 🛠 3. ติดตั้ง Library (ทำแค่ครั้งแรก)

เปิด Terminal เลื่อนเข้าไปที่โฟลเดอร์รันโปรเจกต์นี้ แนะนำให้ลงเครื่องมือดังนี้:
```bash
pip install -r requirements.txt
```
*(หรือถ้ารันไม่ผ่าน ให้ใช้คำสั่งนี้ `pip install fastapi uvicorn langchain langchain-community langchain-text-splitters pypdf chromadb python-multipart ollama`)*

---

## 🚀 4. วิธีเปิดใช้งานระบบ (รันเซิร์ฟเวอร์)

1. เปิด Terminal
2. ตรวจสอบให้แน่ใจว่าอยู่ในโฟลเดอร์เดียวกับไฟล์ `main.py`
3. พิมพ์คำสั่งรันเซิร์ฟเวอร์:
```bash
uvicorn main:app --reload
```
4. เปิด **Web Browser** แล้วเข้าไปที่ลิงก์นี้เพื่อใช้งาน: 👉 **http://127.0.0.1:8000/docs**

---

## 🧪 5. วิธีทดสอบและใช้งานจริงผ่านหน้า Web (Swagger UI)

บนหน้าเว็บ `http://127.0.0.1:8000/docs` คุณจะเจอตัวเลือก API ให้กดทดสอบได้ตามลำดับดังนี้:

### สเต็ปที่ 1: อัปโหลดไฟล์โจทย์
- คลิก **`POST /ingest`**
- กด **"Try it out"**
- อัปโหลดไฟล์ PDF (เช่น `vector_problem_th.pdf`) เข้าไป
- กด **"Execute"** เพื่อให้ AI อ่านโจทย์และจำใส่ความจำ (ดู Code ด้านล่างต้องเป็น `200`)

### สเต็ปที่ 2: เริ่มทดสอบการตรวจของ AI
คุณสามารถโยนก้อนข้อมูล **JSON** เข้าไปให้ 3 API ต่อไปนี้ลองทำงาน (อย่าลืมลบของเก่าแล้วแปะตย. นี้ไปแทน)

**1. ขอคำใบ้ (นักศึกษายังไม่ได้โค้ด)** ➔ **`POST /api/hint`**
```json
{
  "student_question": "ถ้าอาร์เรย์ vector ของผมมันเต็มแล้ว ผมต้องทำยังไงครับ มืดแปดด้าน",
  "problem_topic": "vector data structure"
}
```

**2. วิเคราะห์โค้ด (ส่งงาน)** ➔ **`POST /api/analyze`**
```json
{
  "student_code": "void push_back(int val) { arr[size] = val; size++; }",
  "problem_topic": "vector data structure"
}
```

**3. ดูพัฒนาการ (ตรวจโค้ดเก่า-ใหม่)** ➔ **`POST /api/compare`**
```json
{
  "old_code": "void push(int val) { arr[s++] = val; }",
  "new_code": "void push(int val) { if (s == cap) resize(); arr[s++] = val; }",
  "problem_topic": "vector data structure"
}
```

*(หมายเหตุ: ทุกครั้งที่กด Execute ของ AI อาจจะต้องรอโหลดประมาณ 10-15 วินาที เนื่องจากโมเดล LLM กำลังสร้างคำตอบสดๆ ขึ้นมา)*

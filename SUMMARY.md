# AI Tutor (Vector Problem) - Project Summary

เอกสารนี้เป็นการสรุปสถานะล่าสุดของโปรเจกต์ **AI Tutor** สำหรับโจทย์โครงสร้างข้อมูลและอัลกอริทึม (อัปเดตล่าสุด)

## 📁 โครงสร้างและไฟล์สำคัญ
- **`main.py`**: ไฟล์หลักของเซิร์ฟเวอร์ (FastAPI) ทำหน้าที่รับ Request ควบคุม Routing และเก็บตัวแปร `MOCK_QUESTIONS_DB` ซึ่งตอนนี้บรรจุโจทย์ให้ฝึกทำทั้งหมด **14 ข้อ**
- **`ai_service.py`**: ศูนย์กลางของ AI จัดการโครงสร้าง System Prompt (Hint, Analyze, Compare) ตามสเปกที่วางไว้ และตั้งค่าให้เรียกใช้โมเดลชื่อ `ai-tutor`
- **`rag_service.py`**: ระบบ Retrieval-Augmented Generation คอยจัดการ Ingest ไฟล์ PDF (หั่นข้อความและแปลงเป็น Vector) เข้าไปใน ChromaDB
- **`index.html`**: หน้า UI (Frontend) สำหรับผู้ใช้งาน เขียนด้วย HTML/CSS โทนสีเข้ม (Dark Mode) เพื่อความสวยงาม และสคริปต์เรียก API
- **`Modelfile`**: ไฟล์สำหรับจูนโมเดล Ollama ตัวใหม่ที่ชื่อ `ai-tutor` โดยมีการตั้งค่า `temperature = 0.3` ให้มีเหตุผล และกำหนด System Prompt ไว้เป็นฐาน
- **`pdfs/`**: โฟลเดอร์เก็บเอกสารเฉลยและทฤษฎีของโจทย์ (PDF) ทั้งหมด 14 ข้อ เพื่อความเป็นระเบียบเรียบร้อย

## 🧠 คำสั่งที่ใช้ในการรันระบบ
เพื่อให้ระบบทำงานได้อย่างสมบูรณ์ ต้องเปิดการทำงาน 2 ส่วนควบคู่กัน:
1. **เปิดเซิร์ฟเวอร์ Backend:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```
2. **เปิด AI Model (ผ่าน Ollama):**
   ```bash
   ollama run ai-tutor
   ```
   *(หมายเหตุ: หากมีการแก้ไข `Modelfile` อย่าลืมรันคำสั่ง `ollama create ai-tutor -f Modelfile` เพื่ออัปเดตโมเดล)*

## 📚 รายชื่อโจทย์ (Mock DB) ปัจจุบัน (q1 – q14)
1. **Merge Two Sorted Vectors** (Easy)
2. **Find Kth Largest Element** (Medium)
3. **Reverse a Vector** (Easy)
4. **Grade Calculation (If-Else)** (Easy)
5. **Two Sum** (Easy)
6. **Maximum Subarray** (Medium)
7. **Palindrome Vector Check** (Easy)
8. **Remove Duplicates from Sorted Vector** (Easy)
9. **Missing Number** (Easy)
10. **Move Zeroes** (Easy)
11. **Best Time to Buy and Sell Stock** (Easy)
12. **Product of Array Except Self** (Medium)
13. **Contains Duplicate** (Easy)
14. **Merge Intervals** (Medium)

## 💡 โหมดการทำงาน (Modes)
1. **🙋‍♂️ ขอคำใบ้ (Hint):** ให้คำใบ้ ทฤษฎี Big O และแนวทาง (ไม่เขียนโค้ดเฉลย) โดยอ้างอิงจากฐานข้อมูล PDF
2. **🔍 ตรวจโค้ด (Analyze):** วิเคราะห์โค้ดที่วางลงไป ตรวจจับบั๊ก แนะนำวิธีปรับปรุงประสิทธิภาพ Time/Space Complexity
3. **⚖️ เทียบโค้ดเก่า-ใหม่ (Compare):** นำโค้ดสองเวอร์ชันมาเทียบกัน และสรุปว่าส่วนไหนดีกว่ากัน หรือลดระดับ Big O ลงได้หรือไม่

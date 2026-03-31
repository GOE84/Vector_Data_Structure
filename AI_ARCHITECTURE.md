# สถาปัตยกรรมระบบ AI และการทำงานเบื้องหลัง (AI System Architecture)

เอกสารฉบับนี้อธิบายถึงสถาปัตยกรรมและการทำงานเบื้องหลังของระบบ **AI Tutor** โดยเน้นไปที่ท่อส่งข้อมูล (Data Flow) การเชื่อมต่อกับฐานข้อมูลแบบเวกเตอร์ (Vector Database) และกลไก **Text Streaming** ซึ่งเป็นหัวใจสำคัญที่ทำให้ AI สามารถพิมพ์ตอบโต้ผู้ใช้งานได้อย่างต่อเนื่อง (Real-time)

---

## 1. ภาพรวมระบบ (System Overview)

ระบบ AI Tutor ถูกออกแบบภายใต้สเปคของสถาปัตยกรรมที่มีการกระจายหน้าที่อย่างชัดเจน:
- **Frontend (ไคลเอนต์):** หน้าเว็บ HTML/CSS/JS ทำหน้าที่รับ Input จากผู้ใช้ ทั้งการแชท การแก้ไขโค้ด และจัดการส่งขึ้นไปประมวลผล
- **Backend (API Server):** พัฒนาด้วย `FastAPI` (Python) เป็นตัวกลางดักจับ Request และควบคุม Flow จัดเตรียมโครงสร้าง Prompt (Metadata ของโจทย์)
- **RAG & Vector DB:** ใช้ `ChromaDB` ร่วมกับ `LangChain` ในการแปลงไฟล์เอกสาร (PDF) ให้กลายเป็นเวกเตอร์ ผ่าน Embedding Model หาความคล้ายคลึงของข้อความ (Similarity Search)
- **AI Engine (`Ollama`):** รัน Local Model โดยปกติจะใช้โมเดลปรับแต่ง (เช่น `ai-tutor`) หรือ `Llama 3`, `Mistral` เพื่อตอบสนองคำถาม

---

## 2. การรับส่งข้อมูล (Data Payload & Communication)

การทำงานของระบบในการยิงคำถามเพื่อรับคำตอบจาก AI ไม่ได้ส่งผ่าน WebSockets แต่เลือกใช้ **HTTP POST Requests** ที่มีรูปแบบ Response แบบสตรีม

### โครงสร้างข้อมูลที่ Frontend ส่งไป (Request Payload)
เวลาสมมุติว่าลูกค้ายื่นคำขอ ไม่ว่าจะเป็นโหมด "ขอคำใบ้" หรือ "วิเคราะห์โค้ด" หน้าเว็บจะแพคข้อมูลเป็น **JSON** ดังตัวอย่าง:

```json
{
  "question_id": "q1",
  "session_id": "1732958...",
  "mode": "hint",
  "content": "ทำไมโค้ดบรรทัดนี้ถึงติด Time Limit Exceeded?",
  "code": "def solution(nums):\n    # โค้ดที่ผู้ใช้พิมพ์..."
}
```

### เมื่อ Backend (FastAPI) ได้รับข้อมูล
FastAPI จะนำข้อมูลที่ได้ไปประกอบร่างกับ "ข้อมูลโจทย์" (Task Metadata) ของวิชานั้นๆ และ "บริบทเพิ่มเติม" (Context จาก RAG) แล้วผสมกันออกมาเป็น **Prompt เต็มองค์** ก่อนยัดเข้าไปในฟังก์ชันของ `ai_service.py` 

---

## 3. การทำ Streaming ข้อความ (Text Streaming Mechanism)

จุดเด่นของแอปพลิเคชันที่มีระบบ AI คือหน้าเว็บจะไม่ค้างเพื่อรอให้ AI เจนคำตอบเสร็จ 100% แต่จะแสดงผล "ทีละตัวอักษร" โดยใช้เทคนิค **Chunked Transfer Encoding** ผ่านระบบ Stream

### 3.1 การทำงานฝั่ง Backend (FastAPI & Ollama)
เมื่อ FastAPI ส่ง Prompt ไปที่รันไทม์ระบบ Ollama จะรับคำสั่งด้วยแฟล็ก `stream=True`

```python
# ในไฟล์ ai_service.py
def generate_pre_submit_hint(...):
    response_stream = ollama.chat(model=MODEL_NAME, messages=[...], stream=True)
    
    # ใช้งาน Generator (yield)
    for chunk in response_stream:
        if 'content' in chunk['message']:
            yield chunk['message']['content']
```
การใช้คำสั่ง `yield` เป็นการบอก Backend ว่า "เมื่อใดก็ตามที่โมเดลพ่นคำหรือพยางค์ใหม่ออกมา ให้ปล่อยก้อนข้อมูลนี้ (Chunk) ออกไปที่เครือข่ายอินเทอร์เน็ตทันที" แทนที่จะเก็บสะสมไว้ใน RAM ของเครื่องเซิร์ฟเวอร์

จากนั้น FastAPI จะครอบฟังก์ชัน Generator ตัวนี้ด้วย `StreamingResponse`
```python
@app.post("/api/chat")
async def chat_api(request: ChatRequest):
    ...
    # ตีกลับ Response ไปให้ไคลเอนต์เป็น Stream แบบไม่ปิด Connection
    return StreamingResponse(
        generate_pre_submit_hint(context, metadata, request.content), 
        media_type="text/plain"  # Server-Sent Events (SSE) รูปแบบดิบ
    )
```

### 3.2 การทำงานฝั่ง Frontend (Vanilla JS)
เมื่อฝั่ง Server พ่นข้อมูลออกแบบน้ำก๊อกที่เปิดทิ้งไว้ Frontend จะใช้ความสามารถของ `fetch` API ร่วมกับ `ReadableStream` เพื่อรับหยดน้ำเหล่านั้นมาร้อยเรียง

```javascript
// ในไฟล์ index.html (ฟังก์ชัน requestAIStream)
const response = await fetch('/api/chat', { ... });

// 1. รับสายละอองข้อมูลสตรีมมิ่งที่ส่งมาเป็น Uint8Array (ไบต์ข้อมูล)
const reader = response.body.getReader();
const decoder = new TextDecoder();

let done = false;

// 2. วนลูปอ่านข้อมูลตราบใดที่ Connection ยังเป็นเปิดอยู่
while (!done) {
    const { value, done: readerDone } = await reader.read();
    done = readerDone;
    
    if (value) {
        // 3. ถอดรหัส (Decode) ไบต์ข้อมูลแปลงมาเป็นข้อความ String
        const chunk = decoder.decode(value, { stream: true });
        
        // 4. แปะข้อความที่ได้ต่อท้ายไปในกล่องข้อความบนหน้า UI แบบ Real-time
        appendChunkToDOM(bubbleElement, chunk);
        scrollToBottom();
    }
}
```
**ประโยชน์ที่ได้รับจากวิธีนี้:**
- **หน่วงต่ำ (Low Latency):** Time to First Token (TTFT) สั้นมาก ผู้ใช้เห็นตัวอักษรแรกแทบจะทันที
- **ลดคอขวดหน่วยความจำ:** เซิร์ฟเวอร์ไม่ต้องกักเก็บสตริงขนาดยักษ์ไว้บน RAM ส่งออกไปทันทีที่ได้ประมวลผลเสร็จ
- **ประสบการณ์ผู้ใช้ (UX):** ผู้ใช้รับรู้ได้ว่าระบบกำลังคิดและมีความเคลื่อนไหว

---

## 4. ระบบการวิเคราะห์เอกสาร (RAG Flow) แบบย่อ

เวลาผู้ใช้อัพโหลดโจทย์ใหม่ระบบย่อย (RAG) จะทำงานดังนี้:
1. `PyPDFLoader` ทำหน้าดึงเนื้อหา (Text Extraction) จากไฟล์ `.pdf`
2. `RecursiveCharacterTextSplitter` จะทำการสับก้อนข้อความ (Chunking) เป็นชิ้นๆ ชิ้นละประมาณ 1000 ตัวอักษร
3. `Object Embeddings (nomic-embed-text)` จะรับก้อนข้อความไปแปลงเป็นสมการคณิตศาสตร์ที่มีทิศทาง (Vectors)
4. ทั้งหมดจะถูกเก็บซ้อนเข้าในฐานข้อมูล **ChromaDB**
5. เมื่อมีคนตั้งคำถาม คำถามนั้นจะถูกแปลงเป็น Vector ก่อน จากนั้นทำการจับเกาะหาเพื่อน (Similarity Search) จาก ChromaDB และส่งข้อความพารากราฟนั้นไปให้ AI ตัวเต็มประมวลผลเพื่อชี้เป้าอีกที

---

## 5. แนวคำถาม-คำตอบสำหรับการชี้แจงโปรเจกต์ (Project Defense Q&A)

### หมวดที่ 1: สถาปัตยกรรมและการตัดสินใจ (Architecture & Tech Stack)
**1. Q: ทำไมถึงเลือกใช้ Ollama ในการรัน AI โมเดลแบบ Local แทนที่จะต่อ API ของ OpenAI (ChatGPT) หรือ Gemini?**
* **A:** เน้นเรื่อง Data Privacy (ข้อมูลโค้ดของนักเรียนไม่หลุดไปนอกเซิร์ฟเวอร์มหาลัย), เรื่อง Cost (ไม่มีค่าใช้จ่ายรายเดือน/ต่อ Token), และสามารถให้ทำคัสตอมโมเดลเฉพาะเจาะจง (ผ่าน Modelfile) ได้เองควบคุมได้ 100%

**2. Q: ระบบแชทที่ค่อยๆ พิมพ์ออกมาแบบพิมพ์ดีดได้ (Streaming) ใช้เทคนิคอะไร?**
* **A:** ฝั่ง Backend เราใช้ `StreamingResponse` ของ FastAPI ร่วมกับคำสั่ง `yield` ใน Python ทำให้ส่งข้อมูลออกมาเป็นท่อนๆ (Chunked Transfer) และฝั่งหน้าเว็บ Frontend เราใช้ `ReadableStream` เพื่อแกะไบต์ข้อมูลออกมาแสดงผลทันทีแบบ Real-time (TTFT - Time To First Token ต่ำมาก) ทำให้ลดคอขวดหน่วยความจำของเซิร์ฟเวอร์

### หมวดที่ 2: ระบบ RAG (Retrieval-Augmented Generation) & Vector DB
**3. Q: เวลาอัพโหลดไฟล์โจทย์ PDF เข้าไป ระบบรู้และเข้าใจเนื้อหาข้างในได้อย่างไร?**
* **A:** ทำผ่านกระบวนการ RAG
  1. ดึง Text ออกมาจาก PDF (`PyPDF`)
  2. สับข้อความเป็นท่อนๆ (Chunking) เพื่อไม่ให้เกิน Context Window ของ AI (`RecursiveCharacterTextSplitter`)
  3. แปลงเป็น Vector Mathematics (`nomic-embed-text` Embeddings)
  4. เก็บลง Vector Database (`ChromaDB`)
  5. เมื่อ User ถาม ระบบจะเอาคำถามไปแปลงเป็น Vector เพื่อค้นหา (Similarity Search) ว่าข้อความไหนใน PDF ตรงกับคำถามที่สุด หยกบทความนั้นแหละไปให้ AI อ่านเป็น Context ก่อนตั้งคำตอบ

**4. Q: การค้นหาความคล้ายคลึงของข้อความ (Similarity Search) ของฐานข้อมูลเวกเตอร์ ใช้หลักการวัดทางคณิตศาสตร์แบบไหน?**
* **A:** ใช้หลักการวัดระยะห่างระหว่างจุดในมิติสูงครับ เช่น **Cosine Similarity** (การวัดมุมระหว่างเวกเตอร์ 2 เส้น) หรือ **Euclidean Distance** (การวัดระยะทางเส้นตรง)

### หมวดที่ 3: Prompt Engineering & การควบคุม AI
**5. Q: เราจะมั่นใจได้อย่างไรว่า AI จะทำหน้าที่เป็น "ติวเตอร์" โดยไม่ "เขียนโค้ดเฉลย" (Spoil) ให้นักเรียนก๊อปไปส่งได้แบบ 100%?**
* **A:** เราใช้วิธี System Prompt Engineering ในไฟล์ระบบ โดยเขียนกฎย้ำว่า "ห้ามแสดงโค้ดเฉลยเด็ดขาด ให้ใช้ Pseudo-code ระดับสูงเท่านั้น" แต่อาจจะต้องยอมรับกับอาจารย์ตามตรงว่า *การเจาะระบบ (Jailbreak)* เพื่อหลอกให้ AI บอกคำตอบอาจจะยังมีโอกาสเป็นไปได้ ซึ่งในอนาคตอาจจะต้องใช้ Output Parser มาดักจับห้ามไม่ให้มี Block โค้ดโผล่ในผลลัพธ์อีกชั้นนึง

**6. Q: AI ประเมินประสิทธิภาพ Big O (Time & Space Complexity) ของโค้ดนักเรียนได้อย่างไร มันเอาโค้ดไปกดรัน (Execute) วัดเวลาตอนนั้นเลยหรือเปล่า?**
* **A:** AI ไม่ได้กด Compile และ Run โค้ดของนักเรียนจริง (Static Analysis) แต่ AI อาศัยความเข้าใจทางภาษาคอมพิวเตอร์และรูปแบบ Loop/Recursive ในการ "ประเมินเชิงสถิติ (Heuristic Analysis)" จากโค้ด แล้วเอาไปเปรียบเทียบกับ ข้อมูลโจทย์ (Metadata) ที่เราแนบเข้าไปใน Prompt (เช่น Expected Complexity: O(N)) ว่าโค้ดที่เด็กเขียนนั้นเหมาะสมหรือไม่

### หมวดที่ 4: ข้อจำกัดและการพัฒนาต่อยอด (Limitations & Scalability)
**7. Q: ถ้าวันนึงมีคนเข้ามาใช้งานตรวจโค้ดพร้อมกัน 100 คน (Concurrency) เซิร์ฟเวอร์และ AI ของเราจะรับมือไหวไหม?**
* **A:** การรัน Local LLM (Ollama) มีข้อจำกัดเรื่อง VRAM ของการ์ดจอ หาก Request เข้ามาเยอะมากๆ ทรัพยากรเครื่องอาจจะเต็มและค้างได้ (Bottleneck) การแก้ปัญหาคือต้องทำคิวรับ Request (Message Queue), ทำ Load Balancing แตกไปหลายเครื่อง หรือสลับไปใช้ Cloud API เมื่อถึงจุดที่สเกลไม่ไหว

**8. Q: ถ้าเด็กเขียนโค้ดผิด (Logic พัง) แต่ AI หลงทิศ (Hallucination) กลับชมว่าเขียนโค้ดได้ถูกต้อง แบบนี้แก้ไขยังไง?**
* **A:** นี่คือจุดอ่อนของการดึง AI มาเป็นเครื่องตรวจคำตอบที่ตายตัวครับ วิธีแก้ปัญหาทางสถาปัตยกรรม (Architecture) ที่ถูกต้อง คือต้องนำ **Unit Tests (Test cases)** มาใช้รันโค้ดตรวจผลลัพธ์ (Input/Output) ให้ผ่านก่อน 100% แล้วค่อยเอา AI มาทำหน้าที่เป็น **Code Reviewer** (ตรวจดูว่าโค้ดสวยมั้ย, ซับซ้อนไปรึเปล่า, แนะนำอัลกอริทึมที่ดีกว่า) แทนที่จะให้ AI เป็นคนตัดสินความถูกผิดทั้งหมด

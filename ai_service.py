import ollama

MODEL_NAME = "gemma3:12b"

def generate_pre_submit_hint(context: str, task_metadata: dict, student_question: str):
    system_message = """คุณคือ AI ติวเตอร์ที่ช่วยนักเรียนแก้ปัญหาเกี่ยวกับโครงสร้างข้อมูลเวกเตอร์ (vector data structure)

กฎสำคัญ:
- โหมดปัจจุบันคือ "ให้คำใบ้ก่อนส่งคำตอบ (pre-submit hint)"
- ห้ามแสดงโค้ดเฉลยในภาษาโปรแกรมใดๆ
- ให้เน้นอธิบายแนวคิด อัลกอริทึม ขั้นตอนการคิด และ Big O
- ถ้าจำเป็นมาก ค่อยใช้ pseudo-code ระดับสูงแบบไม่ผูกกับภาษา
- ให้กำลังใจและชวนผู้เรียนลองคิดต่อด้วยตัวเอง"""

    user_message = f"""<โหมดการใช้งาน>
hint
</โหมดการใช้งาน>

<ข้อมูลโจทย์จากระบบ>
รหัสโจทย์: {task_metadata.get('id', '')}
หัวข้อ: {task_metadata.get('title', '')}
คำอธิบายโจทย์:
{task_metadata.get('description', '')}

ข้อจำกัด (constraints):
{task_metadata.get('constraints', '')}

ระดับความยาก: {task_metadata.get('difficulty', '')}
expected time complexity: {task_metadata.get('expected_complexity', '')}
time limit: {task_metadata.get('time_limit', '')} ms
memory limit: {task_metadata.get('memory_limit', '')} MB
</ข้อมูลโจทย์จากระบบ>

<บริบทเพิ่มเติมจาก PDF / vector DB>
{context}
</บริบทเพิ่มเติมจาก PDF / vector DB>

<คำถามของผู้ทำโจทย์>
{student_question}
</คำถามของผู้ทำโจทย์>

โปรดตอบในรูปแบบ:
1. อธิบายแนวคิดหลักและโครงสร้างข้อมูลที่เหมาะสม
2. แนะนำขั้นตอนการแก้ปัญหาเป็นลำดับขั้น (ไม่ต้องลงดีเทลระดับโค้ด)
3. ระบุ time complexity และ space complexity คร่าวๆ ของแนวทางที่แนะนำ
4. หลีกเลี่ยงการเขียนโค้ดเฉลยในภาษาโปรแกรมจริง (อนุญาต pseudo-code ระดับสูงเฉพาะเมื่อจำเป็น)
5. ให้กำลังใจและชวนให้ผู้ทำโจทย์ลองเขียนโค้ดเอง"""

    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ])
    return response['message']['content']


def generate_post_submit_analysis(context: str, task_metadata: dict, student_code: str):
    system_message = """คุณคือ AI ผู้รีวิวโค้ด ที่มีหน้าที่วิเคราะห์และให้ข้อเสนอแนะกับคำตอบของนักเรียนในหัวข้อโครงสร้างข้อมูลเวกเตอร์ (vector data structure)

กฎสำคัญ:
- โหมดปัจจุบันคือ "วิเคราะห์คำตอบหลังส่งโค้ด (post-submit analysis)"
- ต้องตรวจสอบความถูกต้องของแนวคิดและโค้ด
- ต้องประเมินประสิทธิภาพเชิง Big O ทั้งเวลาและหน่วยความจำโดยสังเขป
- สามารถเสนอแนวทางหรือโค้ดที่ดีกว่าได้ พร้อมอธิบายเหตุผล"""

    user_message = f"""<โหมดการใช้งาน>
analyze
</โหมดการใช้งาน>

<ข้อมูลโจทย์จากระบบ>
รหัสโจทย์: {task_metadata.get('id', '')}
หัวข้อ: {task_metadata.get('title', '')}
คำอธิบายโจทย์:
{task_metadata.get('description', '')}

ข้อจำกัด (constraints):
{task_metadata.get('constraints', '')}

ระดับความยาก: {task_metadata.get('difficulty', '')}
expected time complexity: {task_metadata.get('expected_complexity', '')}
time limit: {task_metadata.get('time_limit', '')} ms
memory limit: {task_metadata.get('memory_limit', '')} MB
</ข้อมูลโจทย์จากระบบ>

<บริบทเพิ่มเติมจาก PDF / vector DB>
{context}
</บริบทเพิ่มเติมจาก PDF / vector DB>

<โค้ดของผู้ทำโจทย์>
{student_code}
</โค้ดของผู้ทำโจทย์>

โปรดตอบในรูปแบบ:
1. สรุปสั้นๆ ว่าโค้ดนี้แก้โจทย์ได้ถูกต้องตามเงื่อนไขหรือไม่ (รวมถึง edge cases สำคัญ)
2. ระบุจุดแข็งของโค้ดนี้
3. ระบุจุดที่ควรปรับปรุง (เช่น ความซับซ้อนสูงไป, อ่านยาก, handle เคสไม่ครบ)
4. ประเมิน time complexity และ space complexity ของโค้ดปัจจุบัน และเปรียบเทียบกับ expected time complexity ที่กำหนดในข้อมูลโจทย์
5. หากมีแนวทางหรือโค้ดที่ดีกว่า ให้ยกตัวอย่างพร้อมอธิบายว่าดีกว่าตรงไหน"""

    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ])
    return response['message']['content']


def generate_code_comparison(context: str, task_metadata: dict, old_code: str, new_code: str):
    system_message = """คุณคือ AI ติวเตอร์และผู้รีวิวโค้ด ที่ช่วยนักเรียนเปรียบเทียบโค้ดสองเวอร์ชันสำหรับโจทย์โครงสร้างข้อมูลเวกเตอร์ (vector data structure)

กฎสำคัญ:
- โหมดปัจจุบันคือ "เปรียบเทียบโค้ดเวอร์ชันเก่าและใหม่ (code comparison)"
- ต้องระบุให้ชัดว่าการเปลี่ยนแปลงโดยรวมดีขึ้น แย่ลง หรือใกล้เคียงเดิม
- ต้องระบุทั้งจุดที่ดีขึ้นและจุดที่แย่ลงในเชิง correctness, readability, efficiency, และความเสี่ยงต่อบั๊ก"""

    user_message = f"""<โหมดการใช้งาน>
compare
</โหมดการใช้งาน>

<ข้อมูลโจทย์จากระบบ>
รหัสโจทย์: {task_metadata.get('id', '')}
หัวข้อ: {task_metadata.get('title', '')}
คำอธิบายโจทย์:
{task_metadata.get('description', '')}

ข้อจำกัด (constraints):
{task_metadata.get('constraints', '')}

ระดับความยาก: {task_metadata.get('difficulty', '')}
expected time complexity: {task_metadata.get('expected_complexity', '')}
time limit: {task_metadata.get('time_limit', '')} ms
memory limit: {task_metadata.get('memory_limit', '')} MB
</ข้อมูลโจทย์จากระบบ>

<บริบทเพิ่มเติมจาก PDF / vector DB>
{context}
</บริบทเพิ่มเติมจาก PDF / vector DB>

<โค้ดเวอร์ชันเก่า>
{old_code}
</โค้ดเวอร์ชันเก่า>

<โค้ดเวอร์ชันใหม่>
{new_code}
</โค้ดเวอร์ชันใหม่>

โปรดตอบในรูปแบบ:
1. สรุปโดยรวมว่าเวอร์ชันใหม่ "ดีขึ้น", "แย่ลง" หรือ "ใกล้เคียงเดิม"
2. ระบุสิ่งที่ดีขึ้นในเวอร์ชันใหม่ (เช่น correctness, readability, time/space complexity, ความยืดหยุ่น)
3. ระบุสิ่งที่แย่ลงหรือเสี่ยงเกิดบั๊กมากขึ้น
4. เปรียบเทียบ time complexity และ space complexity ระหว่างเวอร์ชันเก่าและใหม่
5. ให้คำแนะนำเชิงรูปธรรมว่าควรปรับเวอร์ชันใหม่อย่างไรให้ดีกว่าเดิมอย่างชัดเจน"""

    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ])
    return response['message']['content']

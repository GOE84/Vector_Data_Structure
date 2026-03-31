import ollama

DEFAULT_MODEL = "ai-tutor-qwen"
MODEL_MAP = {
    "qwen": "ai-tutor-qwen",
    "gemma": "ai-tutor-gemma",
}

def generate_title_from_text(text: str, model_name: str = DEFAULT_MODEL) -> str:
    system_message = "คุณคือติวเตอร์ที่ต้องช่วยตั้งชื่อหัวข้อโจทย์ปัญหาที่บรรยายใน text สั้นๆ ตั้งชื่อให้กระชับ ไม่เกิน 1 บรรทัด (ประมาณ 3-10 คำ) และห้ามใส่เครื่องหมายคำพูดครอบ ห้ามอธิบายเพิ่มเติม"
    user_message = f"จากเนื้อหาต่อไปนี้ ช่วยตั้งชื่อโจทย์ปัญหาให้หน่อย:\n\n{text[:2000]}"

    try:
        response = ollama.chat(model=model_name, messages=[
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': user_message}
        ])

        if 'message' in response and 'content' in response['message']:
            return response['message']['content'].strip(' "\'')
    except Exception as e:
        print(f"Error generating title: {e}")

    return "Untitled Problem"


def generate_pre_submit_hint(context: str, task_metadata: dict, student_question: str, model_name: str = DEFAULT_MODEL):
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

    response_stream = ollama.chat(model=model_name, messages=[
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ], stream=True)
    for chunk in response_stream:
        if 'message' in chunk and 'content' in chunk['message']:
            yield chunk['message']['content']


def generate_post_submit_analysis(context: str, task_metadata: dict, student_code: str, model_name: str = DEFAULT_MODEL):
    system_message = """คุณคือ AI ติวเตอร์ตรวจโค้ดที่อธิบายเก่ง กระชับ และเข้าใจง่าย

กฎสำคัญ:
- โหมดปัจจุบันคือ "วิเคราะห์คำตอบหลังส่งโค้ด"
- ให้คำวิเคราะห์ที่สั้น ตรงประเด็น ไม่เยิ่นเย้อ
- ใช้ภาษาเป็นกันเอง เข้าใจง่าย อ่านปุ๊บรู้เรื่องปั๊บ
- ประเมินความถูกต้องและประสิทธิภาพ Big O ให้ชัดเจน"""

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

โปรดตอบให้กระชับและเข้าใจง่ายที่สุด โดยแบ่งเป็น 3 หัวข้อดังนี้:
1. 🎯 **ผลการตรวจ:** โค้ดนี้ทำงานถูกต้องครอบคลุมไหม? มีลืมคิดเคสไหนหรือเปล่า? (อธิบายสั้นๆ 1-2 บรรทัด)
2. ⚡ **ประสิทธิภาพ (Big O):** Time/Space Complexity ของโค้ดนี้คืออะไร และผ่านเกณฑ์ที่โจทย์กำหนดหรือไม่?
3. 💡 **คำแนะนำ & โค้ดที่เร็วกว่า:** แนะนำจุดที่ควรแก้ให้โค้ดคลีนขึ้น หรือถ้ามีวิธีที่เร็วกว่าให้ยกตัวอย่างโค้ดสั้นๆ พร้อมอธิบายจุดสำคัญ"""

    response_stream = ollama.chat(model=model_name, messages=[
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ], stream=True)
    for chunk in response_stream:
        if 'message' in chunk and 'content' in chunk['message']:
            yield chunk['message']['content']


def generate_code_comparison(context: str, task_metadata: dict, old_code: str, new_code: str, model_name: str = DEFAULT_MODEL):
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

    response_stream = ollama.chat(model=model_name, messages=[
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ], stream=True)
    for chunk in response_stream:
        if 'message' in chunk and 'content' in chunk['message']:
            yield chunk['message']['content']

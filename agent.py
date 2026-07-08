import os
import re
import docx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

MODEL = "tencent/hy3:free"
# При необходимости замените модель на актуальную бесплатную.


def load_docx_text(path):
    try:
        doc = docx.Document(path)
        return "\n".join(
            p.text.strip()
            for p in doc.paragraphs
            if p.text.strip()
        )
    except Exception as e:
        print(f"Ошибка загрузки документа: {e}")
        return ""


def split_document(text):
    """
    Разбивает документ на логические разделы.
    """

    blocks = []
    current = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        new_block = (
            re.match(r"^\d+(\.\d+)*", line)
            or line.isupper()
        )

        if new_block and current:
            blocks.append("\n".join(current))
            current = []

        current.append(line)

    if current:
        blocks.append("\n".join(current))

    return blocks


DOCUMENT = load_docx_text("Pravilo_1.docx")
BLOCKS = split_document(DOCUMENT)


def search_in_document(question, limit=5):

    words = [
        w.lower()
        for w in re.findall(r"\w+", question)
        if len(w) > 2
    ]

    scored = []

    for block in BLOCKS:

        text = block.lower()

        score = 0

        for word in words:
            score += text.count(word)

        if score > 0:
            scored.append((score, block))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [block for _, block in scored[:limit]]


def ask_agent(question):

    if not DOCUMENT:

        return {
            "answer": "Документ Pravilo_1.docx не найден.",
            "sources": []
        }

    results = search_in_document(question)

    if not results:

        return {
            "answer": "По вашему вопросу ничего не найдено в документе.",
            "sources": []
        }

    context = "\n\n=============================\n\n".join(results)

    try:

        response = client.chat.completions.create(

            model=MODEL,

            temperature=0.2,

            max_tokens=800,

            messages=[

                {
                    "role": "system",
                    "content":
                    (
                        "Ты помощник по документу "
                        "'Правила управления коммерческой деятельностью'.\n\n"

                        "Отвечай только по документу.\n"

                        "Если ответ содержится в нескольких разделах — объедини их.\n"

                        "Не придумывай информацию.\n"

                        "Если информации недостаточно — честно сообщи об этом."
                    )
                },

                {
                    "role": "user",
                    "content":
                    f"""
Документ:

{context}

Вопрос:

{question}
"""
                }

            ]
        )
        from pprint import pprint

        print("=" * 100)
        pprint(response.model_dump())
        print("=" * 100)

        message = response.choices[0].message
        
        answer = message.content
        
        if not answer:
            answer = "Модель не вернула текстовый ответ."

        return {

            "answer": answer,

            "sources": [

                {

                    "section": f"Раздел {i}",

                    "content": block,

                    "warning": "штраф" in block.lower(),

                    "prohibited": "запрещ" in block.lower()

                }

                for i, block in enumerate(results, 1)

            ]

        }

    except Exception as e:

        return {

            "answer": f"Ошибка при обращении к OpenRouter:\n{e}",

            "sources": []

        }
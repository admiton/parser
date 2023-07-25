from PyPDF2 import PdfReader
import re
import json

reader = PdfReader('info.pdf')


def parse_question(text):
    parsed_dict = {"question": "", "answers": [], "code": ""}

    if "Alg" in text and "EndAlg" in text:
        algo_match = re.search(r'(Alg.*EndAlg)', text, re.DOTALL)
        parsed_dict["code"] = algo_match.group(1).strip() if algo_match else ''
        # remove the code section from the text
        text = text.replace(parsed_dict["code"], '')

    answers_match = re.search(r'([A-Z]\..*)', text, re.DOTALL)
    answers_text = answers_match.group(1).strip() if answers_match else ''

    # remove the answers section from the text
    text = text.replace(answers_text, '')

    parsed_dict["question"] = text.strip()

    # parsing answers
    answers_list = re.findall(
        r'([A-Z])\.(.*?)(?=(?:[A-Z]\.|$))', answers_text, re.DOTALL)
    parsed_dict["answers"] = [{key: value.strip()}
                              for key, value in answers_list] if answers_list else []

    return parsed_dict


text = ""

for i in range(len(reader.pages)):
    page = reader.pages[i]

    page_text = page.extract_text()
    text += page_text

lines = text.split('\n')

# print(text)

questions = []
current_question = []
correct_answers = []

# 0 - questions, 1 - answers
category = 1

for line in lines:
    if re.match(r'BAB', line.strip()):
        category ^= 1

    if category:
        # if the line starts with digits, followed by period, we remove the digits
        if re.match(r'\d+\.', line):
            line = re.sub(r'\d+\. ', '', line)

        # if the line contains points, we remove them, and also the digits
        if re.search(r' \d\.?\d* points', line):
            line = re.sub(r' \d*\.?\d* points', '', line)

        line = line.strip()

        if re.match(r'^[A-D]+$', line):
            correct_answers.append(line)
    else:
        # if the line starts with a digit followed by a period, it's the start of a new question
        if re.match(r'\d+\.', line.strip()):
            if current_question:
                questions.append('\n'.join(current_question))
            current_question = [line.strip()]
        else:
            current_question.append(line.strip())

if current_question:
    questions.append('\n'.join(current_question))

questions = questions[1:]

# for question in questions:
#     print(question)
#     print('------------------')


for answer in correct_answers:
    print(answer)

# for question in questions:
#     if question.strip():
#         parsed_questions.append(parse_question(question))

# parsed_questions = json.dumps(parsed_questions, indent=4, ensure_ascii=False)

# print(parsed_questions)

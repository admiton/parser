from PyPDF2 import PdfReader
import re
import json

reader = PdfReader("2022.pdf")


def adjust_answer(line):
    # if the line starts with digits, followed by period, we remove the digits
    if re.match(r"\d+\.", line):
        line = re.sub(r"\d+\. ", "", line)

    # if the line contains points, we remove them, and also the digits
    if re.search(r"\d\.?\d* points", line):
        line = re.sub(r"\d*\.?\d* points", "", line)

    line = line.strip()

    return line


can_strip = 1


def adjust_question(line):
    global can_strip
    # arrange the line, so each answer is on a new line
    if re.search(r"[A-D]\.", line):
        line = re.sub(r"([A-D]\.)( )?", r"\n\1\n", line)
    # we want to have clearly the algorithm separated between the Algorithm and EndAlg
    if re.search(r"Alg", line):
        line = re.sub(r"(\d+\. *)?(Alg\w*)( *)(.*$)", r"\2\n\n\4", line)
        can_strip ^= 1

    if re.search(r"EndAlg", line):
        line = re.sub(r"(\d+\. *)?(EndAlg\w*)( *)(.*$)", r"\1\n\n\3", line)
        can_strip ^= 1

    line = line.rstrip()

    line = line.lstrip() if can_strip else line

    return line


def parse_question(text):
    parsed_dict = {"question": "", "answers": [], "code": ""}

    # extract the answers from the question
    answers_match = re.search(r"([A-D]\..*)", text, re.DOTALL)
    answers_text = answers_match.group(1).strip() if answers_match else ""

    # remove the answers section from the text
    text = text.replace(answers_text, "")

    # extract the code from the question
    code_match = re.search(r"((Alg\w*)(.*?)(EndAlg\w*))", text, re.DOTALL)
    code_text = code_match.group(1).strip() if code_match else ""

    # remove the code section from the text
    text = text.replace(code_text, "")

    # remove all the empty lines from the text
    text = re.sub(r"\n+", "\n", text)

    # now, all the remaining text is the question, so it can be on a single line
    text = text.replace("\n", " ")

    # remove the question number
    text = re.sub(r"^\d+\. ?", "", text)

    parsed_dict["question"] = text
    parsed_dict["code"] = code_text

    # parsing answers
    answers_list = re.findall(
        r"([A-Z])\.(.*?)(?=(?:[A-Z]\.|$))", answers_text, re.DOTALL
    )
    parsed_dict["answers"] = (
        [{key: value.strip()} for key, value in answers_list] if answers_list else []
    )

    return parsed_dict


text = ""

for i in range(len(reader.pages)):
    page = reader.pages[i]

    page_text = page.extract_text()
    text += page_text

lines = text.split("\n")

questions = []
current_question = []
correct_answers = []

# 0 - questions, 1 - answers
category = 1

for line in lines:
    if re.match(r"BAB", line.strip()):
        category ^= 1

    if category:
        line = adjust_answer(line)

        if re.match(r"^[A-D]+$", line):
            correct_answers.append(line)
    else:
        line = adjust_question(line)
        # if the line starts with a digit followed by a period, it's the start of a new question
        if re.match(r" *\d+\. \w", line):
            if current_question:
                questions.append("\n".join(current_question))
            current_question = [line]
        else:
            current_question.append(line)

if current_question:
    questions.append("\n".join(current_question))

questions = questions[1:]

parsed_questions = []

for question in questions:
    if question.strip():
        questions_properties = parse_question(question)
        # add the correct answer to the question
        # questions_properties["correct_answers"] = correct_answers.pop(0)
        # add index to the question
        questions_properties["index"] = len(parsed_questions) + 1
        parsed_questions.append(questions_properties)

parsed_questions = json.dumps(parsed_questions, indent=4, ensure_ascii=False)

# with open('questions2022.json', 'w', encoding='utf-8') as f:
#     f.write(parsed_questions)

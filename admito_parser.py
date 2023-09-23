from PyPDF2 import PdfReader
import re
import json


class PdfParser:
    def __init__(self):
        self.can_strip = 1

    def adjust_answer(self, line):
        # if the line starts with digits, followed by period, we remove the digits
        if re.match(r"\d+.", line):
            line = re.sub(r"\d+. ", "", line)

        # if the line contains points, we remove them, and also the digits
        if re.search(r" 3 puncte", line):
            line = re.sub(r"3 puncte", "", line)

        # remove all the (, ) groups
        line = re.sub(r", ", "", line)

        line = line.strip()

        return line

    def adjust_question(self, line):
        # arrange the line, so each answer is on a new line
        if re.search(r"[A-D]\.", line):
            line = re.sub(r"([A-D]\.)( )?", r"\n\1\n", line)
        # we want to have clearly the algorithm separated between the Algorithm and EndAlg
        if re.search(r"EndAlg", line):
            line = re.sub(r"(\d+\. *)?(EndAlg\w*)( *)(.*$)", r"\2\n\n\4", line)
            self.can_strip ^= 1

        if re.search(r"Alg", line):
            line = re.sub(r"(\d+\. *)?(Alg\w*)( *)(.*$)", r"\2 \4", line)
            self.can_strip ^= 1

        line = line.rstrip()

        line = line.lstrip() if self.can_strip else line

        return line

    def parse_question(self, text, correct_answers):
        parsed_dict = {"text": "",
                       "code": "", "explanation": "", "answers": []}
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

        parsed_dict["text"] = text
        parsed_dict["code"] = code_text
        parsed_dict["explanation"] = ""

        # parsing answers
        answers_list = re.findall(
            r"([A-D])\.(.*?)(?=(?:[A-D]\.|$))", answers_text, re.DOTALL)

        for ans in answers_list:
            obj = {"text": ans[1]}
            if ans[0] in correct_answers:
                obj["isCorrect"] = True
            parsed_dict["answers"].append(obj)

        return parsed_dict

    def parse_pdf(self, filename, pgs=40):
        # pgs -> how many pages to parse

        reader = PdfReader(filename)

        text = ""

        for i in range(min(len(reader.pages), pgs)):
            page = reader.pages[i]

            page_text = page.extract_text()
            text += page_text

        return text

    def parse_text(self, text):
        lines = text.split("\n")

        questions = []
        current_question = []
        correct_answers = []

        # 0 - questions, 1 - answers
        category = 1

        for line in lines:
            if re.search(r"UNIVERS", line.strip()):
                category ^= 1

            if category:
                line = self.adjust_answer(line)

                if re.match(r"^[A-D]+$", line):
                    correct_answers.append(line)
            else:
                line = self.adjust_question(line)
                # if the line starts with a digit followed by a period, it's the start of a new question
                if re.match(r" *\d+\w?\. {1,3}\w", line):
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
                if (correct_answers):
                    questions_properties = self.parse_question(
                        question, correct_answers[0])
                    correct_answers.pop(0)
                    parsed_questions.append(questions_properties)

        return parsed_questions

    def pdf_to_json(self, filename, pgs=40):
        text = self.parse_pdf(filename, pgs)
        parsed_questions = self.parse_text(text)

        parsed_questions = json.dumps(
            parsed_questions, indent=4, ensure_ascii=False)
        return parsed_questions


# Usage example:
if __name__ == "__main__":
    pdf_parser = PdfParser()
    filename = "2022-septembrie.pdf"
    parsed_questions = pdf_parser.pdf_to_json(filename)

    with open("questions.json", "w") as f:
        f.write(parsed_questions)

import json
import os
import sys
import requests
from admito_parser import parse_text, parse_pdf

from PyPDF2 import PdfMerger


def merge_pdfs(_pdfs):
    mergeFile = PdfMerger()

    for i, _pdf in enumerate(_pdfs):
        if i == 1:
            mergeFile.append(_pdf, pages=(0, 1))
        else:
            mergeFile.append(_pdf)

    mergeFile.write("file.pdf")


from bs4 import BeautifulSoup
import urllib.request

url = "https://www.cs.ubbcluj.ro/admitere/nivel-licenta/subiecte-din-anii-precedenti/"


if __name__ == "__main__":
    # merge_pdfs(
    #     [
    #         "Informatica%20iulie%202022%20EN.pdf",
    #         "Informatica%20raspunsuri%20%28toate%20limbile%29%20iulie%202022.pdf",
    #     ]
    # )

    req = requests.get(url)
    soup = BeautifulSoup(req.text, "html.parser")

    urls = []
    for link in soup.find_all("a"):
        url = link.get("href")

        # we only care about multiple choice questions (2021 and beyond)
        if (
            any(str(year) in url for year in range(2021, 2025))
            and url.endswith(".pdf")
            and "Informatica" in url
        ):
            urls.append(url)

    subjects_texts = []

    subject_folder_names = []

    # for i, url in enumerate(urls):
    #     print(i, url)

    for i, url in enumerate(urls):
        if "raspunsuri" in url or "solutii" in url:
            # skip, we handled this in the previous iteration
            continue

        # if url contains word 'RO' replace it with 'EN'
        if "RO" in url:
            url = url.replace("RO", "EN")

        # download current file
        filename = url.split("/")[-1]
        urllib.request.urlretrieve(url, filename)

        subject_folder_names.append(filename)

        # check if it has a pair or answers
        if "raspunsuri" in urls[i + 1] or "solutii" in urls[i + 1]:
            # combine the two pdfs
            filename2 = urls[i + 1].split("/")[-1]
            urllib.request.urlretrieve(urls[i + 1], filename2)

            merge_pdfs([filename, filename2])

            text = parse_pdf("file.pdf")
            parsed_questions = parse_text(text)
            subjects_texts.append(parsed_questions)

            os.remove("file.pdf")

        else:
            text = parse_pdf(filename)
            subjects_texts.append(text)

        # delete the file
        os.remove(filename)

    subjects_texts = json.dumps(subjects_texts, indent=4, ensure_ascii=False)

    # for each question, make a folder with that name, and inside create a json file with the question
    # for i, subject in enumerate(subjects_texts):
    #     subject_folder_name = subject_folder_names[i].split(".")[0]
    #     os.mkdir(subject_folder_name)
    #     with open(f"{subject_folder_name}/questions.json", "w") as f:
    #         f.write(subject)

    with open("questions.json", "w") as f:
        f.write(subjects_texts)

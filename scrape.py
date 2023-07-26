import json
import os
import requests
import urllib.request
import admito_parser
from bs4 import BeautifulSoup
from PyPDF2 import PdfMerger


class AdmitoParser:
    def __init__(self):
        self.admito_parser = admito_parser.PdfParser()
        self.url = "https://www.cs.ubbcluj.ro/admitere/nivel-licenta/subiecte-din-anii-precedenti/"
        self.subjects_texts = []
        self.subject_folder_names = []

    def merge_pdfs(self, _pdfs):
        mergeFile = PdfMerger()

        for i, _pdf in enumerate(_pdfs):
            if i == 1:
                mergeFile.append(_pdf, pages=(0, 1))
            else:
                mergeFile.append(_pdf)

        mergeFile.write("file.pdf")

    def download_and_parse(self):
        req = requests.get(self.url)
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

            self.subject_folder_names.append(filename)

            # check if it has a pair of answers
            if "raspunsuri" in urls[i + 1] or "solutii" in urls[i + 1]:
                # combine the two pdfs
                filename2 = urls[i + 1].split("/")[-1]
                urllib.request.urlretrieve(urls[i + 1], filename2)

                self.merge_pdfs([filename, filename2])

                text = self.admito_parser.parse_pdf("file.pdf")
                parsed_questions = self.admito_parser.parse_text(text)
                self.subjects_texts.append(parsed_questions)

                # os.remove("file.pdf")
            else:
                text = self.admito_parser.parse_pdf(filename)
                self.subjects_texts.append(text)

            # delete the file
            os.remove(filename)

        self.subjects_texts = json.dumps(
            self.subjects_texts, indent=4, ensure_ascii=False)

    def save_to_json_file(self):
        with open("questions.json", "w") as f:
            f.write(self.subjects_texts)


# Usage example:
if __name__ == "__main__":
    admito_parser = AdmitoParser()
    admito_parser.download_and_parse()
    admito_parser.save_to_json_file()

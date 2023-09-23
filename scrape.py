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
        self.sessions = []

    def merge_pdfs(self, _pdfs):
        mergeFile = PdfMerger()

        for i, _pdf in enumerate(_pdfs):
            if i == 1:
                mergeFile.append(_pdf, pages=(0, 1))
            else:
                mergeFile.append(_pdf)

        # delete pdf from index 0
        os.remove(_pdfs[0])

        # write to new pdf
        mergeFile.write(_pdfs[0])

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

            # get session from url
            session = url.split("/")[5]

            if url.split("/")[6] == "concurs":
                session += "-" + url.split("/")[6]
            elif len(session) == 4:
                session += "-" + url.split("/")[7]

            filename = url.split("/")[-1]

            # download file, saving each one in a new folder
            urllib.request.urlretrieve(url, filename)

            # check if it has a pair of answers
            if "raspunsuri" in urls[i + 1] or "solutii" in urls[i + 1]:
                # combine the two pdfs
                filename2 = urls[i + 1].split("/")[-1]
                urllib.request.urlretrieve(urls[i + 1], filename2)

                # get the second page from the new pdf
                self.merge_pdfs([filename, filename2])
                os.remove(filename2)

            parsed_questions = self.admito_parser.pdf_to_json(filename)

            # replace each % 20 with a space
            os.rename(filename, session + ".pdf")

            # create the folder if it doesn't exist
            if not os.path.exists(session):
                os.makedirs(session)

            # move the pdf to the folder
            os.replace(session + ".pdf", session +
                       "/" + session + ".pdf")

            # save the parsed questions to a json file
            with open(session + "/" + session + ".json", "w") as f:
                f.write(parsed_questions)


# Usage example:
if __name__ == "__main__":
    admito_parser = AdmitoParser()
    admito_parser.download_and_parse()

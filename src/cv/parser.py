from docx import Document


class CVParser:
    def __init__(self, file_path):
        self.document = Document(file_path)

    def get_text(self):
        text = []

        for paragraph in self.document.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text.strip())

        return "\n".join(text)

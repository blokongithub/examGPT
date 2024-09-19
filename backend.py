import os
import re
import textwrap
from dotenv import load_dotenv
from openai import OpenAI
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

load_dotenv()
api_key = os.getenv("API_KEY")

client = OpenAI(api_key=api_key)
model = "gpt-4o-mini"

def startup():
    # Define the folder names
    folder_names = ["questions", "answers", "qpdf", "apdf"]
    
    for folder_name in folder_names:
        if not os.path.exists(folder_name):
            # If the folder doesn't exist, create it
            os.makedirs(folder_name)
            if folder_name in ["qpdf", "apdf"]:
                with open(f"{folder_name}/{folder_name}000000000.pdf", "w") as file:
                    file.write("This is a placeholder file.")
            else:
                with open(f"{folder_name}/{folder_name}000000000.txt", "w") as file:
                    file.write("This is a placeholder file.")
            print(f"Folder '{folder_name}' created.")
        else:
            print(f"Folder '{folder_name}' already exists.")

def get_next_id(folder_name, extension):
    files = os.listdir(folder_name)
    ids = []
    for file_name in files:
        match = re.match(rf'{folder_name}(\d+)\.{extension}$', file_name)
        if match:
            ids.append(int(match.group(1)))
    if ids:
        return max(ids) + 1
    else:
        return 1  # Start from 1 if no files are present

def generate_exam_questions(exam: str, board: str, subject: str, questions: int):
    output = ""
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": f"make exam booklet for {exam} style content for {board} board for {subject} subject for {questions} questions, in the format of \n 1) <question> \n 2) <question> \n no awnsers to be provided, just the questions, do not break it up into sections and only provide the questions, no header or footer and how many marks each question is worth after the question in brackets, i.e. (x marks)."}],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            output += chunk.choices[0].delta.content
    return output

def generate_exam_awnsers(questions: str, exam: str, board: str, subject: str):
    output = ""
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": f"provide mark scheme to the following questions \n {questions} for {exam} style content for {board} board for {subject} subject \n awnsers to be provided in the same order as the questions, they will be formatted as 1) \n     <question> \n     - x marks for ... \n     - y marks for ... \n     - z marks for .. ect \n no footer, no header, just mark scheeme"}],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            output += chunk.choices[0].delta.content
    return output

def question_to_pdf(input_file, output_file):
    c = canvas.Canvas(output_file, pagesize=letter)
    width, height = letter
    y_position = height - inch

    line_spacing = 0.3 * inch  # Spacing between answer lines
    question_to_line_spacing = 0.25 * inch  # Space between question and lines
    gap_before_lines = 0.3 * inch  # Gap before the answer lines
    gap_after_lines = 0.4 * inch  # Gap after the answer lines and before the next question

    max_width = width - 2 * inch  # Max width for wrapping text

    with open(input_file, 'r', encoding='utf-8') as infile:
        for line in infile:
            line = line.strip()
            if not line:
                continue

            # Match question number, text, and marks
            match = re.match(r'^(\d+)\)\s*(.*)\s*\((\d+)\s*marks?\)$', line)
            if match:
                question_number = match.group(1)
                question_text = match.group(2)
                marks = int(match.group(3))

                text = f"{question_number}) {question_text} ({marks} marks)"

                wrapped_lines = textwrap.wrap(text, width=int(max_width / 6))

                for wrapped_line in wrapped_lines:
                    c.drawString(inch, y_position, wrapped_line)
                    y_position -= question_to_line_spacing

                    if y_position < inch:
                        c.showPage()
                        y_position = height - inch

                # Add gap before answer lines
                y_position -= gap_before_lines

                # Draw answer lines based on the number of marks
                for _ in range(marks):
                    c.line(inch, y_position, width - inch, y_position)
                    y_position -= line_spacing

                    if y_position < inch:
                        c.showPage()
                        y_position = height - inch

                # Add gap after the answer lines
                y_position -= gap_after_lines

            else:
                c.drawString(inch, y_position, line)
                y_position -= 2 * inch
                if y_position < inch:
                    c.showPage()
                    y_position = height - inch

    c.save()

def mark_scheme_to_pdf(input_file, output_file):
    c = canvas.Canvas(output_file, pagesize=letter)
    width, height = letter
    y_position = height - inch

    line_spacing = 0.3 * inch  # Spacing between lines
    gap_after_point = 0.25 * inch  # Gap after each bullet point
    gap_after_question = 0.5 * inch  # Gap after all points of a question

    max_width = width - 2 * inch  # Max width for wrapping text

    with open(input_file, 'r', encoding='utf-8') as infile:
        for line in infile:
            line = line.strip()
            if not line:
                continue

            # Match question number and mark scheme text
            match = re.match(r'^(\d+)\)\s*(.*)\s*$', line)
            if match:
                question_number = match.group(1)
                question_text = match.group(2)

                text = f"{question_number}) \n {question_text}"
                wrapped_lines = textwrap.wrap(text, width=int(max_width / 6))

                for wrapped_line in wrapped_lines:
                    c.drawString(inch, y_position, wrapped_line)
                    y_position -= line_spacing

                    if y_position < inch:
                        c.showPage()
                        y_position = height - inch

            # Check for bullet points in the mark scheme
            elif line.startswith("-"):
                wrapped_lines = textwrap.wrap(line, width=int(max_width / 6))
                for wrapped_line in wrapped_lines:
                    c.drawString(inch + 0.3 * inch, y_position, wrapped_line)
                    y_position -= gap_after_point

                    if y_position < inch:
                        c.showPage()
                        y_position = height - inch

            # Handle gap after each question's mark scheme
            y_position -= gap_after_question
            if y_position < inch:
                c.showPage()
                y_position = height - inch

    c.save()

def genexam(exam, board, subject, questions):
    # Get next IDs for files
    q_id = get_next_id("questions", "txt")
    a_id = get_next_id("answers", "txt")
    qpdf_id = get_next_id("qpdf", "pdf")
    apdf_id = get_next_id("apdf", "pdf")

    # Define file paths
    q_file = f"questions/questions{q_id}.txt"
    a_file = f"answers/answers{a_id}.txt"
    qpdf_file = f"qpdf/qpdf{qpdf_id}.pdf"
    apdf_file = f"apdf/apdf{apdf_id}.pdf"

    # Generate content
    content = generate_exam_questions(exam, board, subject, questions)
    with open(q_file, "w", encoding='utf-8') as file:
        file.write(content)

    answer_content = generate_exam_awnsers(content, exam, board, subject)
    with open(a_file, "w", encoding='utf-8') as file:
        file.write(answer_content)

    # Generate PDFs
    question_to_pdf(q_file, qpdf_file)
    mark_scheme_to_pdf(a_file, apdf_file)

    print(f"Generated question file: {q_file}")
    print(f"Generated answer file: {a_file}")
    print(f"Generated question PDF: {qpdf_file}")
    print(f"Generated answer PDF: {apdf_file}")

    # Return the paths of the generated PDF files
    return qpdf_file, apdf_file

    
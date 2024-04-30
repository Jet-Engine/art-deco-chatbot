import json
import csv


def save_answers_json(answers, output_path):
    with open(output_path, 'w') as file:
        json.dump(answers, file, indent=4)


def save_answers_csv(json_data, output_path):
    with open(output_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        header = ['Question']
        # Add a column for each model in the first entry's answers
        if json_data:
            header.extend([answer['model'] for answer in json_data[0]['answers']])
        writer.writerow(header)

        for item in json_data:
            row = [item['question']]
            row.extend([answer['answer'] for answer in item['answers']])
            writer.writerow(row)


def save_answers_html(json_data, output_path):
    html_content = '<table border="1">\n<tr><th>Question</th>'
    if json_data:
        # Add a header for each model in the first entry's answers
        html_content += ''.join(f'<th>{answer["model"]}</th>' for answer in json_data[0]['answers'])
    html_content += '</tr>\n'

    for item in json_data:
        row = '<tr><td>' + item['question'] + '</td>'
        row += ''.join(
            '<td>' + format_html(answer['answer']) + '</td>'
            for answer in item['answers'])
        row += '</tr>\n'
        html_content += row
    html_content += '</table>'

    with open(output_path, 'w') as file:
        file.write(html_content)


def format_html(text):
    "A simple function to format text with HTML tags based on markdown syntax."
    # Apply basic markdown to HTML conversions
    replacements = {
        '**': '<b>',
        '__': '<b>',
        '*': '<i>',
        '_': '<i>',
        '```': '<code>',
        '`': '<code>',
        '> ': '<blockquote>',
        '\n': '<br>',
        '# ': '<h1>',
        '## ': '<h2>',
        '### ': '<h3>',
        '#### ': '<h4>',
    }

    for md, html in replacements.items():
        text = text.replace(md, html)
    return text


def save_answers_markdown(json_data, output_path):
    with open(output_path, 'w') as file:
        if json_data:
            # Create the header for the table
            header = "| Question | " + " | ".join([answer['model'] for answer in json_data[0]['answers']]) + " |"
            separator = "| --- " * (len(json_data[0]['answers']) + 1) + "|"
            file.write(header + "\n" + separator + "\n")

            for item in json_data:
                # Prepare each cell to ensure it doesn't break the table format
                row = "| " + escape_markdown(item.get('question', '')) + " |"
                answers = item.get('answers', [])
                row += " | ".join(
                    [markdown_cell(answer.get('answer', '')) for answer in answers])
                row += " |\n"
                file.write(row)

def escape_markdown(text):
    """Escapes markdown special characters within text."""
    # Characters to be escaped in markdown
    escape_chars = "\\`*_{}[]()>#+-.!|"
    # Escaping markdown special characters
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    return text

def markdown_cell(text):
    """Prepares text to be displayed in a markdown table cell."""
    # Replaces newlines with <br> to maintain markdown table format
    text = text.replace('\n', '<br>')
    # Escape markdown syntax to prevent breaking the table
    return escape_markdown(text)





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
    # Define styles for the table, rows, and cells
    table_style = 'border="1" style="border-collapse: collapse;"'
    th_style = 'style="padding: 8px; vertical-align: top;"'
    td_style = 'style="padding: 8px; vertical-align: top;"'

    # Start the table and add a header row with the title 'Questions' for the question column
    html_content = f'<table {table_style}>\n<tr><th {th_style}>Questions</th>'
    if json_data:
        # Add a header for each model in the first entry's answers with styles
        html_content += ''.join(f'<th {th_style}>{answer["model"]}</th>' for answer in json_data[0]['answers'])
    html_content += '</tr>\n'

    for item in json_data:
        # Construct a row for each question with answers from each model
        row = f'<tr><td {td_style}>' + item['question'] + '</td>'
        row += ''.join(
            f'<td {td_style}>' + format_html(answer['answer']) + '</td>'
            for answer in item['answers'])
        row += '</tr>\n'
        html_content += row
    html_content += '</table>'

    # Write the HTML content to the specified file
    with open(output_path, 'w') as file:
        file.write(html_content)


def format_html(text):
    "A more comprehensive function to format text with HTML tags based on markdown syntax including lists."
    # Define replacements for simple markdown syntax
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
        '##### ': '<h5>',
        '###### ': '<h6>',
    }

    # Apply replacements
    for md, html in replacements.items():
        text = text.replace(md, html)

    # Handle unordered lists
    lines = text.split('<br>')
    in_list = False
    for i, line in enumerate(lines):
        if line.startswith('* ') or line.startswith('- ') or line.startswith('+ '):
            if not in_list:
                lines[i] = '<ul><li>' + line[2:] + '</li>'
                in_list = True
            else:
                lines[i] = '<li>' + line[2:] + '</li>'
        else:
            if in_list:
                lines[i - 1] = lines[i - 1] + '</ul>'
                in_list = False

    if in_list:
        lines[-1] += '</ul>'

    # Handle ordered lists
    in_list = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith(tuple(f'{num}.' for num in range(1, 10))):
            if not in_list:
                lines[i] = '<ol><li>' + line.split('. ', 1)[1] + '</li>'
                in_list = True
            else:
                lines[i] = '<li>' + line.split('. ', 1)[1] + '</li>'
        else:
            if in_list:
                lines[i - 1] = lines[i - 1] + '</ol>'
                in_list = False

    if in_list:
        lines[-1] += '</ol>'

    return '<br>'.join(lines)


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
                    [escape_markdown(answer.get('answer', '')) for answer in answers])
                row += " |\n"
                file.write(row)


def escape_markdown(text):
    """Escapes markdown special characters within text."""
    text = text.replace('|', '\|')
    text = text.replace('\n', '<br>')
    return text

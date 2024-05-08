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
            for answer in json_data[0]['answers']:
                header.append(answer['model'])
                if answer['llm_duration'] != -1:
                    header.append(answer['model'] + ' LLM Duration')
                if answer['rag_duration'] != -1:
                    header.append(answer['model'] + ' RAG Duration')
        writer.writerow(header)

        for item in json_data:
            row = [item['question']]
            for answer in item['answers']:
                row.append(answer['answer'])
                if answer['llm_duration'] != -1:
                    row.append(answer['llm_duration'])
                if answer['rag_duration'] != -1:
                    row.append(answer['rag_duration'])
            writer.writerow(row)


def save_answers_html(json_data, output_path):
    if json_data:
        num_columns = 1 + len(json_data[0]['answers'])  # Start with one column for questions
        for answer in json_data[0]['answers']:
            if answer['llm_duration'] != -1:
                num_columns += 1
            if answer['rag_duration'] != -1:
                num_columns += 1

    # Calculate the percentage width for each column
    col_width = 100 / num_columns

    table_style = 'width: 100%; border="1" style="border-collapse: collapse;"'
    th_style = f'style="padding: 8px; vertical-align: top; width: {col_width}%;"'
    td_style = f'style="padding: 8px; vertical-align: top; width: {col_width}%;"'

    html_content = f'<table {table_style}>\n<tr><th {th_style}>Questions</th>'
    if json_data:
        for answer in json_data[0]['answers']:
            html_content += f'<th {th_style}>{answer["model"]}</th>'
            if answer['llm_duration'] != -1:
                html_content += f'<th {th_style}>{answer["model"]} LLM Duration</th>'
            if answer['rag_duration'] != -1:
                html_content += f'<th {th_style}>{answer["model"]} RAG Duration</th>'
    html_content += '</tr>\n'

    for item in json_data:
        row = f'<tr><td {td_style}>{item["question"]}</td>'
        for answer in item['answers']:
            row += f'<td {td_style}>{format_html(answer["answer"])}</td>'
            if answer['llm_duration'] != -1:
                row += f'<td {td_style}>{answer["llm_duration"]}</td>'
            if answer['rag_duration'] != -1:
                row += f'<td {td_style}>{answer["rag_duration"]}</td>'
        row += '</tr>\n'
        html_content += row
    html_content += '</table>'

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
            header = "| Question | "
            for answer in json_data[0]['answers']:
                header += f"{answer['model']} | "
                if answer['llm_duration'] != -1:
                    header += f"{answer['model']} LLM Duration | "
                if answer['rag_duration'] != -1:
                    header += f"{answer['model']} RAG Duration | "
            separator = "| --- " * (header.count('|')) + "|"
            file.write(header + "\n" + separator + "\n")

            for item in json_data:
                row = "| " + escape_markdown(item['question']) + " |"
                for answer in item['answers']:
                    row += escape_markdown(answer['answer']) + " |"
                    if answer['llm_duration'] != -1:
                        row += str(answer['llm_duration']) + " |"
                    if answer['rag_duration'] != -1:
                        row += str(answer['rag_duration']) + " |"
                file.write(row + "\n")



def escape_markdown(text):
    """Escapes markdown special characters within text."""
    text = text.replace('|', '\|')
    text = text.replace('\n', '<br>')
    return text

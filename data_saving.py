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
        # Check if answer is a list and join, otherwise use as is
        row += ''.join(
            '<td>' + (', '.join(answer['answer']) if isinstance(answer['answer'], list) else answer['answer']) + '</td>'
            for answer in item['answers'])
        row += '</tr>\n'
        html_content += row
    html_content += '</table>'

    with open(output_path, 'w') as file:
        file.write(html_content)


def save_answers_markdown(json_data, output_path):
    with open(output_path, 'w') as file:
        file.write("# Answers\n\n")
        for item in json_data:
            file.write(f"## Question\n\n{item['question']}\n\n")
            for answer in item['answers']:
                file.write(f"### {answer['model']}\n\n{answer['answer']}\n\n")

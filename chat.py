import os
from utilities import get_config, read_questions
import openai_client as openai_cli
import groq_client as groq_cli
from data_saving import save_answers_json, save_answers_csv, save_answers_html, save_answers_markdown
import ollama_client


def generate_answers(questions, clients, collection_name, main_model, embed_model):
    answers_data = []
    total_questions = len(questions)
    for idx, question in enumerate(questions, 1):
        print(f"Processing question {idx}/{total_questions}: '{question}'")
        question_answers = {'question': question, 'answers': []}
        for model_name, client in clients.items():
            print(f"Querying {model_name}...")
            if 'ollama' in model_name:
                # Assuming 'ollama_rag' can handle the client passing
                answer = ollama_client.rag(question, main_model, embed_model, collection_name)
            else:
                answer = client(question)
            question_answers['answers'].append({'model': model_name, 'answer': answer})
        answers_data.append(question_answers)
        print(f"Completed question {idx}/{total_questions}.")
    return answers_data


def main():
    config = get_config()
    file_path = 'questions.csv'
    questions = read_questions(file_path)
    clients = {
        'ollama_rag': lambda q: ollama_client.rag(q, config),
        'gpt-4': lambda q: openai_cli.ask_gpt4(openai_cli.create_client(config['openai_key']), q),
        'llama3-8b': lambda q: groq_cli.llama3_8b(groq_cli.create_client(config['groq_key']), q),
        'llama3-70b': lambda q: groq_cli.llama3_70b(groq_cli.create_client(config['groq_key']), q),
    }
    answers_data = generate_answers(questions, clients, config['chroma_collection_name'])
    save_answers_json(answers_data, os.path.join(config['evaluation_path'], 'answers.json'))
    save_answers_csv(answers_data, os.path.join(config['evaluation_path'], 'answers.csv'))
    save_answers_html(answers_data, os.path.join(config['evaluation_path'], 'answers.html'))
    save_answers_markdown(answers_data, os.path.join(config['evaluation_path'], 'answers.md'))


if __name__ == "__main__":
    main()

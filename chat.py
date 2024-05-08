import os
import time

from utilities import get_config, read_questions
from data_saving import save_answers_json, save_answers_csv, save_answers_html, save_answers_markdown
import ollama_rag
from litellm import completion


def generate_answers(questions, clients):
    answers_data = []
    total_questions = len(questions)
    for idx, question in enumerate(questions, 1):
        print(f"Processing question {idx}/{total_questions}: '{question}'")
        question_answers = {'question': question, 'answers': []}
        for model_name, client in clients.items():
            print(f"Querying {model_name}...")
            result = client(question)
            answer = result['response']
            # Convert durations to integer milliseconds

            llm_duration = max(int(result['llm_duration'] * 1000), -1)
            rag_duration = max(int(result['rag_duration'] * 1000), -1)
            question_answers['answers'].append({'model': model_name, 'answer': answer,
                                                'llm_duration': llm_duration, 'rag_duration': rag_duration})
        answers_data.append(question_answers)
        print(f"Completed question {idx}/{total_questions}.")
    return answers_data



def ask_llm(model, query):
    base_url = None
    if model.startswith('ollama'):
        base_url = "http://localhost:11434"

    start_time = time.perf_counter()
    response = completion(
        model=model,
        messages=[
            {"role": "user", "content": query},
        ],
        api_base=base_url
    )
    end_time = time.perf_counter()
    duration = end_time - start_time

    return {"response": response.choices[0].message.content, "llm_duration": duration, "rag_duration": -1}


def main():
    config = get_config()
    file_path = config['questions_file_path']
    questions = read_questions(file_path)

    os.environ["OPENAI_API_KEY"] = config['openai_key']
    os.environ['GROQ_API_KEY'] = config['groq_key']

    ollama_rag_client = ollama_rag.create_client(config)

    all_models = {
        "gpt-4": "gpt-4",
        "groq-llama3-8b": "groq/llama3-8b-8192",
        "groq-llama3-70b": "groq/llama3-70b-8192",
        "ollama-llama3": "ollama/llama3",
        "ollama-llama3-70b": "ollama/llama3:70b",
    }

    selected_models = ["gpt-4", "ollama-llama3", "groq-llama3-70b"]

    clients = {}
    for model in selected_models:
        clients[model] = lambda q, m=model: ask_llm(all_models[m], q)
    clients['ollama_rag'] = lambda q: ollama_rag.rag(ollama_rag_client, q)

    answers_data = generate_answers(questions, clients)
    save_answers_json(answers_data, os.path.join(config['evaluation_path'], 'answers.json'))
    save_answers_csv(answers_data, os.path.join(config['evaluation_path'], 'answers.csv'))
    save_answers_html(answers_data, os.path.join(config['evaluation_path'], 'answers.html'))
    # f = open("evaluation/answers.json", "r")
    # answers_data = json.load(f)
    # save_answers_markdown(answers_data, os.path.join(config['evaluation_path'], 'answers.md'))
    # save_answers_html(answers_data, os.path.join(config['evaluation_path'], 'answers.html'))


if __name__ == "__main__":
    main()

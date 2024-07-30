import os
import time
from litellm import completion
import logging
from file_utils import get_config, read_questions
from data_saving import save_answers_json, save_answers_csv, save_answers_html, save_answers_markdown
import rag

logger = logging.getLogger(__name__)


def generate_answers(questions, config, clients):
    answers_data = []
    total_questions = len(questions)
    for idx, question in enumerate(questions, 1):
        print(f"Processing question {idx}/{total_questions}: '{question}'")
        question_answers = {'question': question, 'answers': []}
        for model_name, client in clients.items():
            print(f"Querying {model_name}...")
            result = client(question)
            answer = result['response']
            llm_duration = max(int(result['llm_duration'] * 1000), -1)
            rag_duration = max(int(result['rag_duration'] * 1000), -1)
            question_answers['answers'].append({'model': model_name, 'answer': answer,
                                                'llm_duration': llm_duration, 'rag_duration': rag_duration})
        answers_data.append(question_answers)
        print(f"Completed question {idx}/{total_questions}.\n")
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


def print_and_return(result):
    print("RAG Response:")
    print(result['response'])
    print(f"LLM Duration: {result['llm_duration']:.2f} seconds")
    print(f"RAG Duration: {result['rag_duration']:.2f} seconds")
    print("--------------------")
    return result


def main():
    config = get_config()
    file_path = config['questions_file_path']
    questions = read_questions(file_path)

    os.environ["OPENAI_API_KEY"] = config['openai_key']
    os.environ['GROQ_API_KEY'] = config['groq_key']

    all_models = config['all_models']
    selected_models = config['selected_models']

    clients = {}
    for model in selected_models:
        clients[model] = lambda q, m=model:  print_and_return(
            ask_llm(all_models[m], q))
    clients['ollama_rag'] = lambda q: print_and_return(
        rag.rag(config, q))

    try:
        answers_data = generate_answers(questions, config, clients)
        save_answers_json(answers_data, os.path.join(
            config['evaluation_path'], 'answers.json'))
        save_answers_csv(answers_data, os.path.join(
            config['evaluation_path'], 'answers.csv'))
        save_answers_html(answers_data, os.path.join(
            config['evaluation_path'], 'answers.html'))
        save_answers_markdown(answers_data, os.path.join(
            config['evaluation_path'], 'answers.md'))
    except Exception as e:
        logger.exception("An error occurred during execution:")


if __name__ == "__main__":
    main()

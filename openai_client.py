from openai import OpenAI


def create_client(api_key):
    client = OpenAI(
        api_key=api_key,
    )
    return client


def ask(client, model, query):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": query}],
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)


def ask_gpt4(client, query):
    return ask(client, "gpt-4", query)


def ask_gpt4_turbo(client, query):
    return ask(client, "gpt-4-turbo", query)


def ask_gpt3_5(client, query):
    return ask(client, "gpt-3.5-turbo", query)

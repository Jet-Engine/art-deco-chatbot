from groq import Groq


def create_client(api_key):
    client = Groq(
        api_key=api_key,
    )
    return client


def ask(client, model, query):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": query,
            }
        ],
        model=model,
    )
    return chat_completion.choices[0].message.content


def ask_llama3_8b(client, query):
    return ask(client, "llama3-8b-8192", query)


def ask_llama3_70b(client, query):
    return ask(client, "llama3-70b-8192", query)


def ask_gemma_7b(client, query):
    return ask(client, "gemma-7b-It", query)


def ask_mixtral(client, query):
    return ask(client, "mixtral-8x7b-32768", query)

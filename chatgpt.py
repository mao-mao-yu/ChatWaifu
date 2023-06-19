import openai


def chat(all_text, chat_text, call_name='パイモン'):
    start_sequence = '\n' + str(call_name) + ':'
    restart_sequence = "\nYou: "
    all_text = all_text + restart_sequence
    prompt = all_text + chat_text + start_sequence

    response = openai.Completion.create(
        model="gpt-3.5-turbo",
        prompt=prompt,
        temperature=0.5,
        max_tokens=1000,
        top_p=1.0,
        frequency_penalty=0.5,
        presence_penalty=0.0,
        stop=["\nYou:"]
    )
    audio_text = response['choices'][0]['text'].strip()
    all_text = prompt + response['choices'][0]['text'].strip()
    return chat_text, all_text, audio_text


if __name__ == '__main__':
    pass

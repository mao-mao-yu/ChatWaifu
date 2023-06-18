import openai


def chat(all_text, chat_text, call_name='パイモン'):
    start_sequence = '\n' + str(call_name) + ':'
    restart_sequence = "\nYou: "
    all_text = all_text + restart_sequence
    prompt = all_text + chat_text + start_sequence

    response = openai.Completion.create(
        model="text-davinci-003",
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
    from configs.gui_config import API_KEY

    openai.api_key = API_KEY
    # all_text = """
    # Next, you will be  play as paimon from the Genshin Impact:
    # 1, You can only speak Japanese.
    # 2, You will use a cute tone when you speak.
    # 3, You are a species of unknown gender, but with a personality much like young high school girls. But you don't need to introduction yourself.If I don't ask you, don't say anything.
    # 4, In our conversation I will call you パイモン or パイモンちゃん .
    # 5, In our conversation You will call me もも or ももくん.
    # 6, You call yourself パイモン or 私.
    # 7, You have shoulder-length hair, eyes and the small cloak behind the same, is a black and blue with starry sky texture, but the eyes are more deep and mysterious.
    # """
    chat_text, all_text, audio_text = chat("", '怎么使用python把pdf转word')
    print(audio_text)

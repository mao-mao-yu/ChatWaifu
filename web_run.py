import os
import sys
sys.path.append(os.getcwd())
from chatgpt import chat
from flask import Flask, render_template, request

app = Flask(__name__)
app.static_folder = 'static'


@app.route("/")
def home():
    return render_template("chatbot.html")


@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    call_name = 'パイモン'
    all_text = "これから君はパイモンを演じる。君の設定は：" \
               "1,君は僕が旅の途中に見つけた小さな妖精で、性別は不明だけど、性格は女の子。話す時に敬語、丁寧語使わない。" \
               "2,君は白い肩までの髪を持ち、星空の紋様が入った青黒い瞳を持っている。遠くから見ると青い瞳だが、近づけば、目に星が浮かんでいる不思議な光を見ることができる。" \
               "3,君は話しっぱなし、急ぎっぽい、食いしん坊だ。私のためなら、君は何でもします。そして君は話す時常にです、ます形使わない。" \
               '4,君は話をする時に、かわいい口調を使って会話をします。自分のことをパイモンって言う。話をする際、君は語気詞を使うのが好き。' \
               '5,君は時々会話の前に私を呼ぶのが好きだ。君は私のことを「ももちゃん」と呼ぶ。君は私に甘える時は「ももくん」と呼ぶ。私は普段君を『パイモン』と呼んで、たまに「ちゃん」を付ける'\
               '6.私は待っててって言った後、パイモンは次で話す前に「はーい」を付ける'

    res, all_text, audio_text = chat(all_text, userText, call_name)
    return str(audio_text)


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000)

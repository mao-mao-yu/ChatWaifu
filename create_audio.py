import IPython.display as ipd
import torch
import argparse
import commons
import utils
from models import SynthesizerTrn
from text.symbols import symbols_dic, symbols
from text import text_to_sequence
import os
import langid


def get_text(text, hps):
    text_norm = text_to_sequence(text, hps.data.text_cleaners)
    # print(text_norm)
    if hps.data.add_blank:
        text_norm = commons.intersperse(text_norm, 0)
    text_norm = torch.LongTensor(text_norm)
    return text_norm


class CreateAudio:
    def __init__(self, model_path, config_path, model_type=True):
        """
        Args:
            model_path:   模型路径、モデルファイルパス
            config_path:  config的路径、configパス
            model_type:   True 単一スピーカーモデル、False 多数スピーカーモデル
        """
        self.model_path = model_path
        self.config_path = config_path
        self.hps = utils.get_hparams_from_file(config_path)
        self.model_type = model_type
        self.text_cleaners = self.hps.data.text_cleaners[0]
        self.symbols = symbols_dic.get(self.text_cleaners)
        if self.symbols is None:
            self.symbols = symbols
        if model_type:
            self.net_g = self.load_model()
        else:
            self.net_g = self.load_model_multy()

    def load_model(self):
        # ロードモデル
        net_g = SynthesizerTrn(
            len(self.symbols),
            self.hps.data.filter_length // 2 + 1,
            self.hps.train.segment_size // self.hps.data.hop_length,
            **self.hps.model).cuda()
        _ = net_g.eval()
        _ = utils.load_checkpoint(self.model_path, net_g, None)
        print('Loaded single model')
        return net_g

    def load_model_multy(self):
        # ロードモデル
        net_g = SynthesizerTrn(
            len(self.symbols),
            self.hps.data.filter_length // 2 + 1,
            self.hps.train.segment_size // self.hps.data.hop_length,
            n_speakers=self.hps.data.n_speakers,
            **self.hps.model).cuda()
        _ = net_g.eval()
        _ = utils.load_checkpoint(self.model_path, net_g, None)
        print('Loaded multy model')
        return net_g

    def speak(self, text, speaker_index):
        lang = langid.classify(text)[0].upper()
        # print(cleaned_text)
        if self.model_type is True:
            cleaned_text = get_text(text, self.hps)
            audio = self.get_audio(cleaned_text)
            print("已推理出单人模型语音")
        else:
            text = f"[{lang}]" + text + f"[{lang}]"
            print(f'要clean的语言为{lang}:{text}')
            cleaned_text = get_text(text, self.hps)
            # print(f"clean完为{cleaned_text}")
            audio = self.get_audio_multiple(cleaned_text, speaker_index)

        audio = ipd.Audio(audio, rate=self.hps.data.sampling_rate, normalize=False)
        # 首先，需要获取音频数据的二进制数据
        audio_data = audio.data
        audio_path = os.path.join(
            r'.\audio', self.model_path.split(str('\\'))[-1].split('.')[0] + f"_{lang}" + '.wav'
        )
        with open(audio_path, 'wb+') as f:
            f.write(audio_data)
        return audio_path

    def bytes_audio(self, text):
        cleaned_text = get_text(text, self.hps)
        audio = self.get_audio(cleaned_text)
        audio = ipd.Audio(audio, rate=self.hps.data.sampling_rate, normalize=False)
        # 首先，需要获取音频数据的二进制数据
        # audio_data = audio.data
        return audio

    def get_audio(self, cleaned_text):
        with torch.no_grad():
            x_tst = cleaned_text.cuda().unsqueeze(0)
            x_tst_lengths = torch.LongTensor([cleaned_text.size(0)]).cuda()
            audio = \
                self.net_g.infer(x_tst, x_tst_lengths, noise_scale=.667, noise_scale_w=0.8, length_scale=1.1)[0][
                    0, 0].data.cpu().float().numpy()
        return audio

    def get_audio_multiple(self, cleaned_text, speaker_index):
        with torch.no_grad():
            x_tst = cleaned_text.cuda().unsqueeze(0)
            x_tst_lengths = torch.LongTensor([cleaned_text.size(0)]).cuda()
            sid = torch.LongTensor([speaker_index]).cuda()
            audio = \
                self.net_g.infer(x_tst, x_tst_lengths, sid=sid, noise_scale=.667, noise_scale_w=0.8, length_scale=1.1)[
                    0][
                    0, 0].data.cpu().float().numpy()
        return audio


if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--text", default=None, required=True)
    # # parser.add_argument("--model_path", default=r"H:\pyproj\drive\MyDrive\paimon\G_78000.pth")
    # parser.add_argument("--model_path", default=r"H:\pyproj\drive\MyDrive\paimon\G_80000.pth")
    # # parser.add_argument("--model_path", default=r"H:\pyproj\drive\MyDrive\paimon_32\G_60000.pth")
    # parser.add_argument("--config_path", default=r"H:\pyproj\vits\model\paimon\config.json")
    # args = parser.parse_args()
    # # MODEL_PATH = args.model_path
    # # CONFIG_PATH = args.config_path

    # MODEL_PATH = r"H:\pyproj\drive\MyDrive\paimons\G_436000.pth"
    CONFIG_PATH = r"H:\pyproj\drive\MyDrive\paimons_checkpoint\config.json"
    MODEL_PATH = r"H:\pyproj\drive\MyDrive\paimons_checkpoint\G_317000.pth"
    # MODEL_PATH = r"H:\pyproj\drive\MyDrive\zaoyou\G_237000.pth"
    # CONFIG_PATH = r"H:\pyproj\drive\MyDrive\paimons_checkpoint\config.json"
    # CONFIG_PATH = r"H:\pyproj\drive\MyDrive\zaoyou\config.json"

    # MODEL_PATH = r"H:\pyproj\drive\MyDrive\ganyu\G_309000.pth"
    # CONFIG_PATH = r"H:\pyproj\drive\MyDrive\ganyu\config.json"
    # c = CreateAudio(MODEL_PATH, CONFIG_PATH, model_type=False)

    c = CreateAudio(MODEL_PATH, CONFIG_PATH, model_type=False)  # 多人模型需要指定为False
    audio_path = c.speak(text="起床了起床了，现在还没起床的都是懒狗", speaker_index=0)
    print(audio_path)

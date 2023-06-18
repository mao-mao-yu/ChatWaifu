import os

import langid
import librosa
import pyopenjtalk
import soundfile as sf
from pypinyin import lazy_pinyin
import shutil
from multiprocessing.dummy import Pool
import logging
import json
import re
import text
from utils import load_filepaths_and_text


def loader(path):
    with open(path, 'r', encoding='utf-8') as f:
        txt = json.load(f)
        msg = f"{path} loaded"
        logging.info(msg)
    return txt


def writer(path, text):
    with open(path, 'w+', encoding='utf-8') as f:
        f.write(text)
    logging.info(f"The file has been written --> {path} ")


def json_writer(path, text):
    writer(path, json.dumps(text, sort_keys=False, indent=4, separators=(',', ':'), ensure_ascii=False))


def resampling(li):
    path, save_path, key = li
    try:
        if os.path.exists(save_path) is False:
            return False, key
        src_sig, sr = sf.read(path)
        resampled = librosa.resample(src_sig, sr, 22050)
        sf.write(path, resampled, 22050)
        print(f"Resampled {key} to {path} ")
        return True, key
    except Exception as e:
        print(f"Resampling {path} error ==>> {e}")
        return False, key


class SetGenShinData:
    def __init__(self, all_character_path, old_wav_path, save_path):
        logging.basicConfig(level=logging.INFO)
        self.all_character_path = all_character_path
        self.old_wav_path = old_wav_path
        self.save_path = save_path

        self.txt_save_path = r"H:\pyproj\vits\filelists"
        self.lang_li = ['EN', 'JP', 'CHS']
        self.path_dict = {
            'JP': r"H:\jp_wav",
            'CHS': r"H:\cn_wav",
            'EN': r"H:\en_wav"
        }
        self.cleaner_dic = {
            'JP': ["japanese_cleaners2"],
            'CHS': ['chinese_cleaners'],
            'CHS_JP': ["zh_ja_mixture_cleaners"],
            'CHS_EN_JP': ["cje_cleaners"]
        }

        self.all_character_dict = loader(self.all_character_path)

        self.cleaner = None
        self.n_speaker = None
        self.cleaned = False
        self.one_character_dict = {}
        self.new_wav_path = ""
        self.train_path = ""
        self.test_path = ""
        self.speaker_name = ""
        self.lang = ""

    def from_dic_create_data(self, speaker_li):
        speaker, lang = speaker_li
        lang = lang.strip().upper()
        all_character_dict = self.all_character_dict
        cha_dict = {}
        if lang not in self.lang_li:
            logging.warning(f"No data for this language --> {lang}")
        for key in all_character_dict:
            npc_name = all_character_dict.get(key).get('npcName')
            now_lang = all_character_dict.get(key).get('language')
            if npc_name == speaker.strip() and now_lang == lang:
                filename = all_character_dict.get(key).get('fileName')
                text = all_character_dict.get(key).get('text')

                if filename is not None:
                    filename = filename.split('\\')[1:]
                    path = ""
                    for i in filename:
                        path = os.path.join(path, i)
                    path = os.path.join(self.old_wav_path, path)
                    path = path.replace('.wem', '.wav')
                    if text is not None:
                        cha_dict[key] = {
                            'text': text,
                            'filename': path
                        }

        json_save_path = os.path.join(
            self.save_path, self.clean_name(speaker, lang) + "_" + lang + '.json'
        )
        self.new_wav_path = self.path_dict[lang]
        old_path = os.path.join(self.new_wav_path, speaker)
        move_to = os.path.join(self.new_wav_path, self.clean_name(speaker, lang))

        if langid.classify(speaker)[0] is not "es" and os.path.exists(old_path) is True:
            os.rename(old_path, move_to)
            logging.info(f'Rename {old_path} to {move_to}')
        if os.path.exists(move_to) is False:
            logging.warning(f"Path {move_to} not exists")

        cha_dict = self.move_and_resampling(cha_dict, move_to)
        self.one_character_dict = cha_dict
        json_writer(json_save_path, self.one_character_dict)

    def from_dir_create_data(self, speaker_li):
        speaker, lang = speaker_li
        lang = lang.strip().upper()
        if lang not in self.lang_li:
            logging.warning(f"No data for this language --> {lang}")
        self.new_wav_path = self.path_dict[lang]
        key_path = os.path.join(self.new_wav_path, speaker)
        if langid.classify(speaker)[0] is not "es":
            speaker = self.clean_name(speaker, lang)
            new_path = os.path.join(self.new_wav_path, speaker)
            if os.path.exists(new_path) is False:
                os.rename(key_path, new_path)
                logging.info(f'Rename {key_path} to {new_path}')
            key_path = new_path
        if os.path.exists(key_path) is False:
            logging.warning(f"Path {key_path} not exists")
        cha_dict = {}
        fl_li = os.listdir(key_path)
        for filename in fl_li:
            key = filename.split('.')[0]
            data_dic = self.all_character_dict.get(key)
            if data_dic is not None:
                txt = self.all_character_dict.get(key).get('text')
                if txt is not None:
                    cha_dict[key] = {
                        'text': txt,
                        'filename': os.path.join(key_path, key + '.wav')
                    }
                # print(cha_dict)

        self.one_character_dict = cha_dict
        json_save_path = os.path.join(
            self.save_path, speaker + "_" + lang + '.json'
        )

        json_writer(json_save_path, self.one_character_dict)

    def set_data(self, speaker_li, data_num, weight):
        speaker, lang = speaker_li
        lang = lang.strip().upper()
        cleaned_name = self.clean_name(speaker, lang)
        json_save_path = os.path.join(
            self.save_path, cleaned_name + "_" + lang + '.json'
        )
        cha_dict = loader(json_save_path)
        count = 0
        train_text = ''
        test_text = ''
        if data_num is None:
            data_num = len(cha_dict)
        else:
            data_num = int(data_num)
        for key in cha_dict:
            if cha_dict[key]["filename"] is not None:
                if count < weight * data_num:
                    train_text = train_text + cha_dict[key].get('filename') + "|" + cha_dict[key][
                        'text'] + '\n'
                    count += 1
                else:
                    test_text = test_text + cha_dict[key].get('filename') + "|" + cha_dict[key][
                        'text'] + '\n'

        self.train_path = os.path.join(self.txt_save_path, cleaned_name + "_" + lang + '_train_data.txt')
        self.test_path = os.path.join(self.txt_save_path, cleaned_name + "_" + lang + '_test_data.txt')
        self.n_speaker = 1
        self.speaker_name = cleaned_name
        self.lang = lang
        self.cleaner = self.cleaner_dic[lang]

        writer(self.train_path, train_text)
        writer(self.test_path, test_text)

    def set_data_multy(self, speaker_li, data_num, weight):
        # speaker_li = [["",r""],[]]
        train_text = ''
        test_text = ''
        lang_li = []
        for index, [speaker, lang] in enumerate(speaker_li):
            lang = lang.strip().upper()
            if lang not in lang_li:
                lang_li.append(lang)
            cleaned_name = self.clean_name(speaker, lang)
            json_save_path = os.path.join(
                self.save_path, cleaned_name + "_" + lang + '.json'
            )
            cha_dict = loader(json_save_path)
            count = 0
            if data_num is None:
                data_num = len(cha_dict)
            else:
                data_num = int(data_num)
            for key in cha_dict:
                if count < weight * data_num:
                    train_text = train_text + cha_dict[key].get('filename') + '|' + str(
                        int(index)) + "|" + self.add_lang(
                        cha_dict[key]['text'], lang) + '\n'
                    count += 1
                else:
                    test_text = test_text + cha_dict[key].get('filename') + '|' + str(int(index)) + "|" + self.add_lang(
                        cha_dict[key]['text'], lang) + '\n'

        self.train_path = os.path.join(self.txt_save_path, 'multy_train_data.txt')
        self.test_path = os.path.join(self.txt_save_path, 'multy_test_data.txt')
        self.n_speaker = len(speaker_li)
        self.speaker_name = None
        cleaner_key = "_".join(sorted(lang_li))
        self.cleaner = self.cleaner_dic[cleaner_key]
        # print(self.cleaner)

        writer(self.train_path, train_text)
        writer(self.test_path, test_text)

    @staticmethod
    def get_filename(path):
        if os.path.isdir(path):
            raise IsADirectoryError('This is a dir not file...')
        if os.path.exists(path) is not True:
            raise FileNotFoundError("Can't find this file...")
        split_str = os.path.split(path)
        filepath = split_str[0]
        filename = split_str[1]
        if len(filename.split('.')) == 1:
            return './' + filename, filename
        else:
            return filepath, filename.split('.')[0]

    def arrange_json(self):
        all_character_data = self.all_character_dict
        json_filepath, json_filename = self.get_filename(self.all_character_path)
        new_character_dict = {}
        for k, v in all_character_data.items():
            npcname = v.get('npcName')
            text = v.get('text')
            filename = v.get('fileName')
            lang = v.get('language')
            if npcname is not None and text is not None:
                if npcname not in new_character_dict:
                    new_character_dict.update({npcname: {}})
                if lang not in new_character_dict.get(npcname):
                    new_character_dict[npcname].update({lang: {}})

                new_character_dict[npcname][lang].update({k: {'text': text, 'filename': filename}})

        json_path = os.path.join(json_filepath, 'arranged_' + json_filename + '.json')
        # print(json_path)
        json_writer(json_path, new_character_dict)

    def arrange_voice(self, voice_path):
        v_li = os.listdir(voice_path)
        for i in v_li:
            key = i.split('.')[0]
            if self.all_character_dict.get(key) is not None and self.all_character_dict.get(key).get(
                    'npcName') is not None:
                npc_name = self.all_character_dict.get(key).get('npcName')
                now_path = os.path.join(
                    voice_path, i
                )
                npc_path = os.path.join(
                    voice_path, npc_name
                )
                if os.path.exists(npc_path) is False and npc_name != "#{REALNAME[ID(1)|HOSTONLY(true)]}":
                    print("Character path is not exists. Will create")
                    try:
                        os.mkdir(npc_path)
                    except Exception as e:
                        print(f"Create {e} error》 {i},{npc_name}")
                new_path = os.path.join(
                    npc_path, i
                )
                try:
                    if now_path != new_path:
                        shutil.move(now_path, new_path)
                except Exception as e:
                    print(f"Move {e} error")
            else:
                print(f"Can't find {i} in character dict")

    def output_config(self):
        config_path = r"H:\pyproj\vits\configs"
        base_json = loader(r"H:\pyproj\vits\configs\base.json")
        base_json['data']["text_cleaners"] = self.cleaner

        if self.n_speaker == 1:
            base_json['data']["n_speakers"] = 0
        else:
            base_json['data']["n_speakers"] = self.n_speaker

        if self.cleaned is True:
            base_json['data']["cleaned_text"] = self.cleaned
            base_json['data']["training_files"] = self.train_path + '.cleaned'
            base_json['data']["validation_files"] = self.test_path + '.cleaned'
        else:
            base_json['data']["cleaned_text"] = self.cleaned
            base_json['data']["training_files"] = self.train_path
            base_json['data']["validation_files"] = self.test_path

        # resampling_bol = self.one_character_dict.get('resampled')
        # if resampling_bol is False:

        if self.speaker_name is None:
            path = os.path.join(config_path, "multy_base.json")
            json_writer(path, base_json)
        else:
            path = os.path.join(config_path, self.speaker_name + "_" + self.lang + ".json")
            json_writer(path, base_json)

    @staticmethod
    def add_lang(text, lang):
        lang = lang.upper()
        lang_dic = {
            'CHS': 'ZH',
            'JP': 'JA',
            'EN': 'EN'
        }
        lang = lang_dic[lang]
        return f"[{lang}]{text}[{lang}]"

    @staticmethod
    def move_and_resampling(cha_dict, move_to):
        li = []
        for key in cha_dict:
            if type(cha_dict[key]) is bool:
                continue
            path = cha_dict[key].get('filename')
            save_path = os.path.join(move_to, key + '.wav')
            li.append([path, save_path, key])
            cha_dict[key]['filename'] = save_path

        pool = Pool(16)
        res_li = pool.map(resampling, li)

        for bol, key in res_li:
            if bol is False:
                cha_dict.pop(key)
                print(f'Deleted {key}')
        return cha_dict

    @staticmethod
    def clean_name(name, lang):
        lang = lang.upper()  # 传入的lang
        check_lang = langid.classify(name)[0].upper()  # 通过name获取的lang
        print(check_lang)
        lang_dic = {
            'JA': "JP",
            'EN': 'EN',
            'ZH': "CHS"
        }
        if lang_dic[check_lang] != lang:
            lang = lang
        else:
            lang = lang_dic[check_lang]
        if lang == 'EN':
            return name.lower()
        elif lang == 'JP':
            cleaned = ''
            labels = pyopenjtalk.extract_fullcontext(name)
            for label in labels:
                phoneme = re.search(r'(?<=-)(.*?)(?=\+)', label.split('/')[0]).group(1)
                if phoneme != 'sil':
                    cleaned += phoneme
            return cleaned
        elif lang == 'CHS':
            return ''.join(lazy_pinyin(name))
        else:
            print(f'No data for this language--> {lang}')

    def preprocess(self, text_index, text_cleaners, file_li=None):
        if file_li is None:
            if self.train_path is not None and self.test_path is not None:
                file_li = [self.train_path, self.test_path]
            else:
                logging.warning("Train text path and test text path can't be None")

        for filelist in file_li:
            print("START:", filelist)
            filepaths_and_text = load_filepaths_and_text(filelist)
            # print(filepaths_and_text)
            for i in range(len(filepaths_and_text)):
                original_text = filepaths_and_text[i][text_index]
                # print(original_text)
                cleaned_text = text._clean_text(original_text, text_cleaners)
                filepaths_and_text[i][text_index] = cleaned_text

            new_filelist = filelist + "." + 'cleaned'
            with open(new_filelist, "w", encoding="utf-8") as f:
                f.writelines(["|".join(x) + "\n" for x in filepaths_and_text])
        self.cleaned = True

    def run_resampling(self, speaker_li):
        lang = speaker_li[1].upper()
        cleaned_name = self.clean_name(speaker_li[0], lang)
        move_to = os.path.join(self.path_dict.get(lang), cleaned_name)
        json_save_path = os.path.join(
            self.save_path, cleaned_name + "_" + lang + '.json'
        )
        self.one_character_dict = loader(json_save_path)
        bol = self.one_character_dict.get('resampled')
        if bol is not False:
            self.move_and_resampling(self.one_character_dict, move_to)
            self.one_character_dict['resampled'] = False
            json_writer(json_save_path, self.one_character_dict)

    def run(self, speaker_lis, create_method, data_num=None, weight=0.95, train_mode=0):
        func_dic = {
            'dir': self.from_dir_create_data,
            'dic': self.from_dic_create_data
        }
        for li in speaker_lis:
            if func_dic.get(create_method) is None:
                logging.warning(f"Create method is not exists,It will be:{func_dic}")
            else:
                func_dic[create_method](li)

        if train_mode == 0:
            for speaker_li in speaker_lis:
                self.set_data(speaker_li, data_num, weight)
                self.run_resampling(speaker_li)
                self.preprocess(1, self.cleaner)
                self.output_config()
        elif train_mode == 1:
            self.set_data_multy(speaker_lis, data_num, weight)
            for speaker_li in speaker_lis:
                self.run_resampling(speaker_li)
            self.preprocess(2, self.cleaner)
            self.output_config()
        else:
            logging.warning(f"Don't have this mode --> {train_mode}. Only have 0 single or 1 multy")


if __name__ == '__main__':
    character_dict_path = r"H:\pyproj\vits\data\resultv34.json"
    old_wavs_path = r"H:\Merged_Chinese_Wav"
    data_path = r"H:\pyproj\vits\data"

    # print(clean_name('早柚', 'JP'))
    s = SetGenShinData(character_dict_path, old_wav_path=old_wavs_path, save_path=data_path)
    s.arrange_json()
    # s_l = [['早柚', 'JP'], ['早柚', 'chs']]
    # li = [['早柚', 'jp']]
    # li = ['早柚', 'jp']
    # s.run(li, create_method='dir', train_mode=0)
    # s.run_resampling(li)
    # s.from_dir_create_data(li)
    # s_l = [['神里綾華', 'JP'], ['刻晴', 'JP'], ['香菱', 'chs'], ['刻晴', 'CHS']]
    """
    设置好角色list信息之后直接run就完事了
    create_method 两种模式，一种是dic从text json文件找对应的角色和语言，另一种是dir从分类好的已有的语音文件找对应的text,建议用dir
    
    train_mode 有两种0或1 0模式生成的用于训练单人模型，1为角色list综合之后的数据，用于训练多人模型
    """

    # s.arrange_voice(r"H:\en_wav")
    """
    第一步从所有角色json文件或者文件夹 制作出单个角色的数据集
    格式为s.from_dic_create_data('早柚', 'JP')
    """
    # s.from_dic_create_data(['早柚', 'JP'])
    # s.from_dic_create_data(['康纳', 'CHS'])
    # s.from_dic_create_data(['神里绫华', 'CHS'])
    # s.from_dir_create_data(['刻晴', 'JP'])
    # s.from_dir_create_data(['香菱', 'chs'])

    """
    设置单个或者多个speaker的数据集
    单个格式为 s.set_data('早柚', 'JP', data_num=None, weight=0.95)
    多个speaker时为
    speakers = [['早柚', 'JP'], ['早柚', 'CHS']]
    s.set_data_multy(speakers, data_num=None, weight=0.95)
    data_num为想要设置多少条语音文件
    weight为训练集和验证集的比重
    """
    # s.set_data([['刻晴', 'JP']], data_num=None, weight=0.95)
    # speakers = [['早柚', 'JP'], ['早柚', 'CHS']]
    # s.set_data_multy(speakers, data_num=None, weight=0.95)

    # 将文本进行预处理
    # file_li = [r"H:\pyproj\vits\data\zaoyou_train_data.txt", r"H:\pyproj\vits\data\zaoyou_test_data.txt"]
    # s.preprocess(file_li, text_index=1, text_cleaners='chinese_cleaners')

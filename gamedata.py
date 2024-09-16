import json
import os

from PIL import Image


class GameData():
    RESOURCE_FOLDER = "Resources"
    CHARACTER_LIST = ["Squall", "Zell", "Irvine", "Quistis", "Rinoa", "Selphie", "Seifer", "Edea", "Laguna", "Kiros", "Ward", "Angelo",
                      "Griever", "Boko"]
    COLOR_LIST = ["Darkgrey", "Grey", "Yellow", "Red", "Green", "Blue", "Purple", "White",
                  "DarkgreyBlink", "GreyBlink", "YellowBlink", "RedBlink", "GreenBlink", "BlueBlink", "PurpleBlink", "WhiteBlink"]
    LOCATION_LIST = ["Galbadia", "Esthar", "Balamb", "Dollet", "Timber", "Trabia", "Centra", "Horizon"]


    def __init__(self):
        self.devour_values = {}
        self.card_values = {}
        self.card_type_values = {}
        self.magic_values = {}
        self.item_values = {}
        self.status_values = []
        self.status_ia_values = {}
        self.gforce_values = []
        self.magic_type_values = []
        self.stat_values = []
        self.enemy_abilities_values = {}
        self.enemy_abilities_type_values = {}
        self.translate_hex_to_str_table = []
        self.game_info_test = {}
        self.special_action = {}
        self.monster_values = {}
        self.kernel_data_json = []
        self.card_data_json = []
        self.card_image_list = []
        self.__init_hex_to_str_table()

    def __init_hex_to_str_table(self):
        with open("Resources/sysfnt.txt", "r", encoding="utf-8") as localize_file:
            self.translate_hex_to_str_table = localize_file.read()
            self.translate_hex_to_str_table = self.translate_hex_to_str_table.replace(',",",',
                                                                                      ',";;;",')  # Handling the unique case of a "," character (which is also a separator)
            self.translate_hex_to_str_table = self.translate_hex_to_str_table.replace('\n', '')
            self.translate_hex_to_str_table = self.translate_hex_to_str_table.split(',')
            for i in range(len(self.translate_hex_to_str_table)):
                self.translate_hex_to_str_table[i] = self.translate_hex_to_str_table[i].replace(';;;', ',')
                if self.translate_hex_to_str_table[i].count('"') == 2:
                    self.translate_hex_to_str_table[i] = self.translate_hex_to_str_table[i].replace('"', '')

    def load_kernel_data(self, file_path):
        with open(file_path, encoding="utf8") as f:
            self.kernel_data_json = json.load(f)

        for i in range(len(self.kernel_data_json["sections"])):
            if self.kernel_data_json["sections"][i]["section_offset"]:
                self.kernel_data_json["sections"][i]["section_offset"] = int( self.kernel_data_json["sections"][i]["section_offset"], 16)
            if self.kernel_data_json["sections"][i]["section_offset_text_linked"]:
                self.kernel_data_json["sections"][i]["section_offset_text_linked"] = int(self.kernel_data_json["sections"][i]["section_offset_text_linked"], 16)
            if self.kernel_data_json["sections"][i]["section_offset_data_linked"]:
                self.kernel_data_json["sections"][i]["section_offset_data_linked"] = int(self.kernel_data_json["sections"][i]["section_offset_data_linked"], 16)

    def load_card_json_data(self, file_path):
        with open(file_path, encoding="utf8") as f:
            self.card_data_json = json.load(f)
        for key in self.card_data_json["card_data_offset"]:
            self.card_data_json["card_data_offset"][key] = int(self.card_data_json["card_data_offset"][key], 16)
        self.__load_cards()

    def __load_cards(self):
        # Thank you Maki !
        img = Image.open(os.path.join("Resources", "text_0.png"))
        TILES_WIDTH_EL = 128
        TILES_HEIGHT_EL = 128
        for i, list_el in enumerate(self.card_data_json["card_type"]):
            # Calculate the bounding box of the tile
            left = list_el["img_x"] * TILES_WIDTH_EL
            upper = list_el["img_y"] * TILES_HEIGHT_EL
            right = left + TILES_WIDTH_EL
            lower = upper + TILES_HEIGHT_EL
            # Extract the tile using cropping
            tile = img.crop((left, upper, right, lower))
            self.card_data_json["card_type"][i]["img"] = tile

        img = Image.open(os.path.join("Resources", "cards_00.png"))
        img_remaster = Image.open(os.path.join("Resources", "cards_00_remaster.png"))

        TILES_WIDTH = 64
        TILES_HEIGHT = 64
        for i, list_el in enumerate(self.card_data_json["card_info"]):
            # Calculate the bounding box of the tile
            left = list_el["img_x"] * TILES_WIDTH
            upper = list_el["img_y"] * TILES_HEIGHT
            right = left + TILES_WIDTH
            lower = upper + TILES_HEIGHT
            # Extract the tile using cropping
            tile = img.crop((left, upper, right, lower))
            self.card_data_json["card_info"][i]["img"] = tile

        TILES_WIDTH = 256
        TILES_HEIGHT = 256
        for i, list_el in enumerate(self.card_data_json["card_info"]):
            # Calculate the bounding box of the tile
            left = list_el["img_x"] * TILES_WIDTH
            upper = list_el["img_y"] * TILES_HEIGHT
            right = left + TILES_WIDTH
            lower = upper + TILES_HEIGHT
            # Extract the tile using cropping
            tile_remaster = img_remaster.crop((left, upper, right, lower))
            self.card_data_json["card_info"][i]["img_remaster"] =tile_remaster

    def translate_str_to_hex(self, string):
        c = 0
        str_size = len(string)
        encode_list = []
        while c < str_size:
            char = string[c]
            if char == '\\':
                encode_list.append(0x02)
                c += 2
                continue
            if char == '\n':  # \n{NewPage}\n,\n
                if '{NewPage}' in string[c + 1:c + 10]:
                    encode_list.append(0x01)
                    c += 10
                else:
                    encode_list.append(0x02)
                    c += 1
                continue
            elif char == '{':
                rest = string[c + 1:]
                index_next_bracket = rest.find('}')
                if index_next_bracket != -1:
                    substring = rest[:index_next_bracket]
                    if substring in self.CHARACTER_LIST:  # {name}
                        index_list = self.CHARACTER_LIST.index(substring)
                        if index_list < 11:
                            encode_list.extend([0x03, 0x30 + index_list])
                        elif index_list == 11:
                            encode_list.extend([0x03, 0x40])
                        elif index_list == 12:
                            encode_list.extend([0x03, 0x50])
                        elif index_list == 13:
                            encode_list.extend([0x03, 0x60])
                    elif substring in self.COLOR_LIST:  # {Color}
                        index_list = self.COLOR_LIST.index(substring)
                        encode_list.extend([0x06, 0x20 + index_list])
                    elif substring in self.LOCATION_LIST:  # {Location}
                        index_list = self.LOCATION_LIST.index(substring)
                        encode_list.extend([0x0e, 0x20 + index_list])
                    elif 'Var' in substring:
                        if len(substring) == 5:
                            if 'b' in substring:  # {Varb0}
                                encode_list.extend([0x04, int(substring[-1]) + 0x40])
                            else:  # {Var00}
                                encode_list.extend([0x04, int(substring[-1]) + 0x30])
                        else:  # {Var0}
                            encode_list.extend([0x04, int(substring[-1]) + 0x20])
                    elif 'Wait' in substring:  # {Wait000}
                        encode_list.extend([0x09, int(substring[-1]) + 0x20])
                    elif 'Jp' in substring:  # {Jp000}
                        encode_list.extend([0x1c, int(substring[-1]) + 0x20])
                    elif '{' + substring + '}' in self.translate_hex_to_str_table:  # {} at end of sysfnt
                        encode_list.append(self.translate_hex_to_str_table.index('{' + substring + '}'))
                    elif 'x' in substring and len(substring) == 5:  # {xffff}
                        encode_list.extend([int(substring[1:3], 16), int(substring[3:5], 16)])
                    elif 'x' in substring and len(substring) == 3:  # {xff}
                        encode_list.append(int(substring[1:3], 16))
                    c += len(substring) + 2
                    continue
            encode_list.append(self.translate_hex_to_str_table.index(char))
            c += 1
            # Jp ?
        return encode_list

    def translate_hex_to_str(self, hex_list):
        str = ""
        i = 0
        hex_size = len(hex_list)
        while i < hex_size:
            hex_val = hex_list[i]

            if hex_val == 0x00:
                pass
            elif hex_val in [0x01, 0x02]:
                str += self.translate_hex_to_str_table[hex_val]
            elif hex_val == 0x03:  # {Name}
                i += 1
                if i < hex_size:
                    hex_val = hex_list[i]
                    if hex_val >= 0x30 and hex_val <= 0x3a:
                        str += '{' + self.CHARACTER_LIST[hex_val - 0x30] + '}'
                    elif hex_val == 0x40:
                        str += '{' + self.CHARACTER_LIST[11] + '}'
                    elif hex_val == 0x50:
                        str += '{' + self.CHARACTER_LIST[12] + '}'
                    elif hex_val == 0x60:
                        str += '{' + self.CHARACTER_LIST[13] + '}'
                    else:
                        str += "{{x03{:02x}}}".format(hex_val)
                else:
                    str += "{x03}"
            elif hex_val == 0x04:  # {Var0}, {Var00} et {Varb0}
                i += 1
                if i < hex_size:
                    hex_val = hex_list[i]
                    if hex_val >= 0x20 and i <= 0x27:
                        str += "{{Var{:02x}}}".format(hex_val - 0x20)
                    elif hex_val >= 0x30 and i <= 0x37:
                        str += "{{Var0{:02x}}}".format(hex_val - 0x30)
                    elif hex_val >= 0x40 and i <= 0x47:
                        str += "{{Varb{:02x}}}".format(hex_val - 0x40)
                    else:
                        str += "{{x04{:02x}}}".format(hex_val)

                else:
                    str += "{x04}"
            elif hex_val == 0x06:  # {Color}
                i += 1
                if i < hex_size:
                    hex_val = hex_list[i]
                    if hex_val >= 0x20 and hex_val <= 0x2f:
                        str += '{' + self.COLOR_LIST[hex_val - 0x20] + '}'
                    else:
                        str += "{{x06{:02x}}}".format(hex_val)
                else:
                    str += "{x06}"
            elif hex_val == 0x09:  # {Wait000}
                i += 1
                if i < hex_size:
                    hex_val = hex_list[i]
                    if hex_val >= 0x20:
                        str += "{{Wait{:03}}}".format(hex_val - 0x20)
                    else:
                        str += "{{x09{:02x}}}".format(hex_val)
                else:
                    str += "{x06}"
            elif hex_val == 0x0e:  # {Location}
                i += 1
                if i < hex_size:
                    hex_val = hex_list[i]
                    if hex_val >= 0x20 and hex_val <= 0x27:
                        str += '{' + self.LOCATION_LIST[hex_val - 0x20] + '}'
                    else:
                        str += "{{x0e{:02x}}}".format(hex_val)
                else:
                    str += "{x0e}"
            elif hex_val >= 0x019 and hex_val <= 0x1b:  # jp19, jp1a, jp1b
                i += 1
                if i < len(hex_list):
                    old_hex_val = hex_val
                    hex_val = hex_list[i]
                    if hex_val >= 0x20:
                        character = None  # To be changed, caract(index, oldIndex-0x18);
                    else:
                        character = None
                    if not character:
                        character = "{{x{:02x}{:02x}}}".format(old_hex_val, hex_val)
                    str += character
                else:
                    str += "{{x{:02x}}}".format(hex_val)
            elif hex_val == 0x1c:  # addJp
                i += 1
                if i < hex_size:
                    hex_val = hex_list[i]
                    if hex_val >= 0x20:
                        str += "{{Jp{:03}}}".format(hex_val - 0x20)
                    else:
                        str += "{{x1c{:02x}}}".format(hex_val)
                else:
                    str += "{x1c}"
            elif hex_val >= 0x05 and hex_val <= 0x1f:
                i += 1
                if i < hex_size:
                    str += "{{x{:02x}{:02x}}}".format(hex_val, hex_list[i])
                else:
                    str += "{{x{:02x}}}".format(hex_val)
            else:
                character = self.translate_hex_to_str_table[hex_val]  # To be done
                if not character:
                    character = "{{x{:02x}}}".format(hex_val)
                str += character
            i += 1
        return str

    def load_all(self):
        self.load_card_data(os.path.join(self.RESOURCE_FOLDER, "card.txt"))
        self.load_devour_data(os.path.join(self.RESOURCE_FOLDER, "devour.txt"))
        self.load_magic_data(os.path.join(self.RESOURCE_FOLDER, "magic.txt"))
        self.load_item_data(os.path.join(self.RESOURCE_FOLDER, "item.txt"))
        self.load_status_data(os.path.join(self.RESOURCE_FOLDER, "status.txt"))
        self.load_magic_type_data(os.path.join(self.RESOURCE_FOLDER, "magic_type.txt"))
        self.load_stat_data(os.path.join(self.RESOURCE_FOLDER, "stat.txt"))
        self.load_ennemy_abilities_data(os.path.join(self.RESOURCE_FOLDER, "enemy_abilities.txt"))
        self.load_ennemy_abilities_type_data(os.path.join(self.RESOURCE_FOLDER, "enemy_abilities_type.txt"))
        self.load_special_action_data(os.path.join(self.RESOURCE_FOLDER, "special_action.txt"))
        self.load_monster_data(os.path.join(self.RESOURCE_FOLDER, "monster.txt"))
        self.load_status_ai_data(os.path.join(self.RESOURCE_FOLDER, "status_ai.txt"))
        self.load_gforce_data(os.path.join(self.RESOURCE_FOLDER, "gforce.txt"))
        self.load_kernel_data(os.path.join(self.RESOURCE_FOLDER, "kernel_bin_data.json"))
        self.load_card_json_data(os.path.join(self.RESOURCE_FOLDER, "card.json"))

    def load_status_ai_data(self, file):
        with (open(file, "r") as f):
            file_split = f.read().split('\n')
            for el_split in file_split:
                split_line = el_split.split('>')
                self.status_ia_values[int(split_line[0], 10)] = {'name': split_line[1],
                                                                 'ref': str(int(split_line[0], 10)) + ":" + split_line[1]}

    def load_special_action_data(self, file):
        with (open(file, "r") as f):
            file_split = f.read().split('\n')
            for el_split in file_split:
                split_line = el_split.split('>')
                self.special_action[int(split_line[0], 10)] = {'name': split_line[1],
                                                               'ref': str(int(split_line[0], 10)) + ":" + split_line[1]}

    def load_devour_data(self, file):
        with (open(file, "r") as f):
            file_split = f.read().split('\n')
            for el_split in file_split:
                split_line = el_split.split('<')
                self.devour_values[int(split_line[0], 16)] = {'name': split_line[1],
                                                              'ref': str(int(split_line[0], 16)) + ":" + split_line[1]}

    def load_card_data(self, file):
        with (open(file, "r") as f):
            file_split = f.read().split('\n')
            for el_split in file_split:
                split_line = el_split.split('<')
                self.card_values[int(split_line[0], 16)] = {'name': split_line[1],
                                                            'ref': str(int(split_line[0], 16)) + ":" + split_line[1]}

    def load_card_type_data(self, file):
        with (open(file, "r") as f):
            file_split = f.read().split('\n')
            for el_split in file_split:
                split_line = el_split.split('<')
                self.card_type_values[int(split_line[0], 16)] = {'name': split_line[1],
                                                            'ref': str(int(split_line[0], 16)) + ":" + split_line[1]}

    def load_magic_data(self, file):
        with (open(file, "r") as f):
            file_split = f.read().split('\n')
            for el_split in file_split:
                split_line = el_split.split('<')
                self.magic_values[int(split_line[0], 16)] = {'name': split_line[1],
                                                             'ref': str(int(split_line[0], 16)) + ":" + split_line[1]}

    def load_item_data(self, file):
        with (open(file, "r") as f):
            file_split = f.read().split('\n')
            for el_split in file_split:
                split_line = el_split.split('<')
                self.item_values[int(split_line[0], 16)] = {'name': split_line[1],
                                                            'ref': str(int(split_line[0], 16)) + ":" + split_line[1]}

    def load_status_data(self, file):
        with (open(file, "r") as f):
            self.status_values = f.read().split('\n')

    def load_gforce_data(self, file):
        with (open(file, "r") as f):
            self.gforce_values = f.read().split('\n')

    def load_magic_type_data(self, file):
        with (open(file, "r") as f):
            self.magic_type_values = f.read().split('\n')

    def load_stat_data(self, file):
        with (open(file, "r") as f):
            self.stat_values = f.read().split('\n')

    def load_monster_data(self, file):
        with (open(file, "r", encoding='utf8') as f):
            self.monster_values = f.read().split('\n')

    def load_ennemy_abilities_data(self, file):
        with (open(file, "r") as f):
            file_split = f.read().split('\n')
            for el_split in file_split:
                self.enemy_abilities_values[int(el_split.split('>')[0])] = {'name': el_split.split('>')[1],
                                                                             'ref': el_split.split('>')[0] + ":" + el_split.split('>')[1]}

    def load_ennemy_abilities_type_data(self, file):
        with (open(file, "r") as f):
            file_split = f.read().split('\n')
            for el_split in file_split:
                self.enemy_abilities_type_values[int(el_split.split('>')[0])] = {'name': el_split.split('>')[1],
                                                                                  'ref': el_split.split('>')[0] + ":" + el_split.split('>')[1]}

if __name__ == "__main__":
    game_data = GameData()
    game_data.load_all()
    print("Hello, World!")
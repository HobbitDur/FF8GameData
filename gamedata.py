import json
import os

from PIL import Image


class GameData():


    def __init__(self, game_data_submodule_path=""):
        self.resource_folder = os.path.join(game_data_submodule_path, "Resources")
        self.devour_data_json = {}
        self.magic_data_json = {}
        self.gforce_data_json = {}
        self.item_data_json = {}
        self.special_action_data_json = {}
        self.stat_data_json = {}
        self.monster_data_json = {}
        self.status_data_json = {}
        self.sysfnt_data_json = {}
        self.kernel_data_json = {}
        self.__init_hex_to_str_table()

    def __init_hex_to_str_table(self):
        self.load_sysfnt_data()
        with open(os.path.join(self.resource_folder, "sysfnt.txt"), "r", encoding="utf-8") as localize_file:
            self.translate_hex_to_str_table = localize_file.read()
            self.translate_hex_to_str_table = self.translate_hex_to_str_table.replace(',",",',
                                                                                      ',";;;",')  # Handling the unique case of a "," character (which is also a separator)
            self.translate_hex_to_str_table = self.translate_hex_to_str_table.replace('\n', '')
            self.translate_hex_to_str_table = self.translate_hex_to_str_table.split(',')
            for i in range(len(self.translate_hex_to_str_table)):
                self.translate_hex_to_str_table[i] = self.translate_hex_to_str_table[i].replace(';;;', ',')
                if self.translate_hex_to_str_table[i].count('"') == 2:
                    self.translate_hex_to_str_table[i] = self.translate_hex_to_str_table[i].replace('"', '')

    def load_gforce_data(self):
        file_path = os.path.join(self.resource_folder, "gforce.json")
        with open(file_path, encoding="utf8") as f:
            self.gforce_data_json = json.load(f)

    def load_stat_data(self):
        file_path = os.path.join(self.resource_folder, "stat.json")
        with open(file_path, encoding="utf8") as f:
            self.stat_data_json = json.load(f)

    def load_status_data(self):
        file_path = os.path.join(self.resource_folder, "status.json")
        with open(file_path, encoding="utf8") as f:
            self.status_data_json = json.load(f)

    def load_devour_data(self):
        file_path = os.path.join(self.resource_folder, "devour.json")
        with open(file_path, encoding="utf8") as f:
            self.devour_data_json = json.load(f)

    def load_enemy_abilities_data(self):
        file_path = os.path.join(self.resource_folder, "enemy_abilities.json")
        with open(file_path, encoding="utf8") as f:
            self.enemy_abilities_data_json = json.load(f)

    def load_magic_data(self):
        file_path = os.path.join(self.resource_folder, "magic.json")
        with open(file_path, encoding="utf8") as f:
            self.magic_data_json = json.load(f)

    def load_special_action_data(self, file_path):
        file_path = os.path.join(self.resource_folder, "special_action.json")
        with open(file_path, encoding="utf8") as f:
            self.special_action_data_json = json.load(f)

    def load_monster_data(self):
        file_path = os.path.join(self.resource_folder, "monster.json")
        with open(file_path, encoding="utf8") as f:
            self.monster_data_json = json.load(f)

    def load_sysfnt_data(self):
        file_path = os.path.join(self.resource_folder, "sysfnt_data.json")
        with open(file_path, encoding="utf8") as f:
            self.sysfnt_data_json = json.load(f)

    def load_item_data(self):
        file_path = os.path.join(self.resource_folder, "item.json")
        with open(file_path, encoding="utf8") as f:
            self.item_data_json = json.load(f)

    def load_kernel_data(self):
        file_path = os.path.join(self.resource_folder, "kernel_bin_data.json")
        with open(file_path, encoding="utf8") as f:
            self.kernel_data_json = json.load(f)

        for i in range(len(self.kernel_data_json["sections"])):
            if self.kernel_data_json["sections"][i]["section_offset"]:
                self.kernel_data_json["sections"][i]["section_offset"] = int(
                    self.kernel_data_json["sections"][i]["section_offset"], 16)
            if self.kernel_data_json["sections"][i]["section_offset_text_linked"]:
                self.kernel_data_json["sections"][i]["section_offset_text_linked"] = int(
                    self.kernel_data_json["sections"][i]["section_offset_text_linked"], 16)
            if self.kernel_data_json["sections"][i]["section_offset_data_linked"]:
                self.kernel_data_json["sections"][i]["section_offset_data_linked"] = int(
                    self.kernel_data_json["sections"][i]["section_offset_data_linked"], 16)

    def load_card_json_data(self):
        file_path = os.path.join(self.resource_folder, "card.json")
        with open(file_path, encoding="utf8") as f:
            self.card_data_json = json.load(f)
        for key in self.card_data_json["card_data_offset"]:
            self.card_data_json["card_data_offset"][key] = int(self.card_data_json["card_data_offset"][key], 16)
        self.__load_cards()

    def __load_cards(self):
        # Thank you Maki !
        img = Image.open(os.path.join(self.resource_folder, "text_0.png"))
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

        img = Image.open(os.path.join(self.resource_folder, "cards_00.png"))
        img_remaster = Image.open(os.path.join(self.resource_folder, "cards_00_remaster.png"))

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
            self.card_data_json["card_info"][i]["img_remaster"] = tile_remaster

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
                    if substring in self.sysfnt_data_json['Characters']:  # {name}
                        index_list = self.sysfnt_data_json['Characters'].index(substring)
                        if index_list < 11:
                            encode_list.extend([0x03, 0x30 + index_list])
                        elif index_list == 11:
                            encode_list.extend([0x03, 0x40])
                        elif index_list == 12:
                            encode_list.extend([0x03, 0x50])
                        elif index_list == 13:
                            encode_list.extend([0x03, 0x60])
                    elif substring in self.sysfnt_data_json['Colors']:  # {Color}
                        index_list = self.sysfnt_data_json['Colors'].index(substring)
                        encode_list.extend([0x06, 0x20 + index_list])
                    elif substring in self.sysfnt_data_json['Locations']:  # {Location}
                        index_list = self.sysfnt_data_json['Locations'].index(substring)
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
                        str += '{' + self.sysfnt_data_json['Characters'][hex_val - 0x30] + '}'
                    elif hex_val == 0x40:
                        str += '{' + self.sysfnt_data_json['Characters'][11] + '}'
                    elif hex_val == 0x50:
                        str += '{' + self.sysfnt_data_json['Characters'][12] + '}'
                    elif hex_val == 0x60:
                        str += '{' + self.sysfnt_data_json['Characters'][13] + '}'
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
                        str += '{' + self.sysfnt_data_json['Colors'][hex_val - 0x20] + '}'
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
                        str += '{' + self.sysfnt_data_json['Locations'][hex_val - 0x20] + '}'
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
        self.load_monster_data()
        self.load_sysfnt_data()
        self.load_item_data()
        self.load_devour_data()
        self.load_gforce_data()
        self.load_stat_data()
        self.load_status_data()
        self.load_kernel_data()
        self.load_card_json_data()


if __name__ == "__main__":
    game_data = GameData()
    game_data.load_all()
    print("Hello, World!")

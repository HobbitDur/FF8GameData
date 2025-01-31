import copy
import os
from math import floor

from .sequenceanalyser import SequenceAnalyser
from ..GenericSection.ff8text import FF8Text
from ..gamedata import GameData, AIData
from .commandanalyser import CommandAnalyser


class GarbageFileError(IndexError):
    pass


class MonsterAnalyser:
    DAT_FILE_SECTION_LIST = ['header', 'skeleton', 'model_geometry', 'model_animation', 'unknown_section4', 'unknown_section5', 'unknown_section6', 'info_stat',
                             'battle_script', 'sound', 'unknown_section10', 'texture']
    MAX_MONSTER_TXT_IN_BATTLE = 10
    MAX_MONSTER_SIZE_TXT_IN_BATTLE = 100
    NUMBER_SECTION = len(DAT_FILE_SECTION_LIST)

    def __init__(self, game_data):
        self.file_raw_data = bytearray()
        self.origin_file_name = ""
        self.origin_file_checksum = ""
        self.subsection_ai_offset = {'init_code': 0, 'ennemy_turn': 0, 'counter_attack': 0, 'death': 0, 'unknown': 0}
        self.section_raw_data = [bytearray()] * self.NUMBER_SECTION
        self.header_data = copy.deepcopy(game_data.AIData.SECTION_HEADER_DICT)
        self.model_animation_data = copy.deepcopy(game_data.AIData.SECTION_MODEL_ANIM_DICT)
        self.seq_animation_data = copy.deepcopy(game_data.AIData.SECTION_MODEL_SEQ_ANIM_DICT)
        self.info_stat_data = copy.deepcopy(game_data.AIData.SECTION_INFO_STAT_DICT)
        self.battle_script_data = copy.deepcopy(game_data.AIData.SECTION_BATTLE_SCRIPT_DICT)
        self.sound_data = bytes()  # Section 9
        self.sound_unknown_data = bytes()  # Section 10
        self.sound_texture_data = bytes()  # Section 11
        self.was_physical = False
        self.was_magic = False
        self.was_item = False
        self.was_gforce = False

    def __str__(self):
        return "Name: {} \nData:{}".format(self.info_stat_data['monster_name'],
                                           [self.header_data, self.model_animation_data, self.info_stat_data, self.battle_script_data])

    def load_file_data(self, file, game_data):
        self.subsection_ai_offset = {'init_code': 0, 'ennemy_turn': 0, 'counter_attack': 0, 'death': 0, 'unknown': 0}
        self.section_raw_data = [bytearray()] * self.NUMBER_SECTION
        self.header_data = copy.deepcopy(game_data.AIData.SECTION_HEADER_DICT)
        self.model_animation_data = copy.deepcopy(game_data.AIData.SECTION_MODEL_ANIM_DICT)
        self.info_stat_data = copy.deepcopy(game_data.AIData.SECTION_INFO_STAT_DICT)
        self.battle_script_data = copy.deepcopy(game_data.AIData.SECTION_BATTLE_SCRIPT_DICT)
        self.file_raw_data = bytearray()
        with open(file, "rb") as f:
            while el := f.read(1):
                self.file_raw_data.extend(el)
        self.__analyze_header_section(game_data)
        self.origin_file_name = os.path.basename(file)
        # self.origin_file_checksum = get_checksum(file, algorithm='SHA256')

    def analyse_loaded_data(self, game_data: GameData):
        try:
            for i in range(0, self.NUMBER_SECTION - 1):
                self.section_raw_data[i] = self.file_raw_data[self.header_data['section_pos'][i]: self.header_data['section_pos'][i + 1]]

            self.section_raw_data[self.NUMBER_SECTION - 1] = self.file_raw_data[
                                                             self.header_data['section_pos'][self.NUMBER_SECTION - 1]:self.header_data['file_size']]
            # No need to analyze Section 1 : Skeleton
            # No need to analyze Section 2 : Model geometry
            # No need to analyze Section 3 : Model animation
            self.__analyze_model_animation(game_data)
            # No need to analyze Section 4 : Unknown
            # No need to analyze Section 5 : Unknown
            #self.__analyze_sequence_animation(game_data)
            # No need to analyze Section 6 : Unknown
            # Analyzing Section 7 : Informations & stats
            self.__analyze_info_stat(game_data)
            # Analyzing Section 8 : Battle scripts/AI
            self.__analyze_battle_script_section(game_data)
            # No need to analyze Section 9 : Sounds
            # No need to analyze Section 10 : Sounds/Unknown
            # No need to analyze Section 11 : Textures
        except IndexError as e:
            print(f"Garbage file {self.origin_file_name}")
            raise GarbageFileError
        except Exception as e:
            print(e)

    def write_data_to_file(self, game_data: GameData, dat_path):
        print("Writing monster {}".format(self.info_stat_data["monster_name"].get_str()))
        raw_data_to_write = bytearray()

        # Write the 7 (0 to 6) first section as raw data
        for i, section_data in enumerate(self.section_raw_data):
            if i < 7:
                raw_data_to_write.extend(section_data)
            else:
                break
        # For the 3rnd, just changing nb animation after
        section_offset = self.header_data['section_pos'][3]
        start_animation = section_offset + AIData.SECTION_MODEL_ANIM_NB_MODEL['offset']
        end_animation = section_offset + AIData.SECTION_MODEL_ANIM_NB_MODEL['offset'] + AIData.SECTION_MODEL_ANIM_NB_MODEL['size']
        raw_data_to_write[start_animation:end_animation] = self.model_animation_data['nb_animation'].to_bytes(
            byteorder=AIData.SECTION_MODEL_ANIM_NB_MODEL['byteorder'], length=AIData.SECTION_MODEL_ANIM_NB_MODEL['size'])

        section_position = 7
        self.section_raw_data[section_position] = bytearray()
        for param_name, value in self.info_stat_data.items():
            property_elem = [x for ind, x in enumerate(AIData.SECTION_INFO_STAT_LIST_DATA) if x['name'] == param_name][0]
            if param_name in ([x['name'] for x in game_data.stat_data_json['stat']] + ['card', 'devour']):  # List of 1 byte value
                value_to_set = bytes(value)
            elif param_name in ['med_lvl', 'high_lvl', 'extra_xp', 'xp', 'ap', 'nb_animation', 'padding']:
                value_to_set = value.to_bytes(length=property_elem['size'], byteorder=property_elem['byteorder'])
            elif param_name in ['low_lvl_mag', 'med_lvl_mag', 'high_lvl_mag', 'low_lvl_mug', 'med_lvl_mug', 'high_lvl_mug', 'low_lvl_drop',
                                'med_lvl_drop',
                                'high_lvl_drop']:  # Case with 4 values linked to 4 IDs
                value_to_set = []
                for el2 in value:
                    value_to_set.append(el2['ID'])
                    value_to_set.append(el2['value'])
                value_to_set = bytes(value_to_set)
            elif param_name in ['mug_rate', 'drop_rate']:  # Case with %
                value_to_set = round((value * 255 / 100)).to_bytes()
            elif param_name in ['elem_def']:  # Case with elem
                value_to_set = []
                for i in range(len(value)):
                    value_to_set.append(floor((900 - value[i]) / 10))
                value_to_set = bytes(value_to_set)
            elif param_name in ['status_def']:  # Case with elem
                value_to_set = []
                for i in range(len(value)):
                    value_to_set.append(value[i] + 100)
                value_to_set = bytes(value_to_set)
            elif param_name in AIData.ABILITIES_HIGHNESS_ORDER:
                value_to_set = bytearray()
                for el2 in value:
                    value_to_set.extend(el2['type'].to_bytes())
                    value_to_set.extend(el2['animation'].to_bytes())
                    value_to_set.extend(el2['id'].to_bytes(2, property_elem['byteorder']))
                value_to_set = bytes(value_to_set)
            elif param_name in AIData.BYTE_FLAG_LIST:
                byte = 0
                for i, bit in enumerate(value.values()):
                    byte |= (bit << i)
                value_to_set = bytes([byte])
            elif param_name in ['monster_name']:
                value.fill(24)
                value_to_set = value.get_data_hex()
            elif param_name in ['renzokuken']:
                value_to_set = bytearray()
                for i in range(len(value)):
                    value_to_set.extend(value[i].to_bytes(2, AIData.SECTION_INFO_STAT_RENZOKUKEN['byteorder']))
            else:  # Data that we don't modify in the excel
                print("Data not taken into account !")
                continue
            if value_to_set:
                self.section_raw_data[section_position].extend(value_to_set)
                # self.file_raw_data[self.header_data['section_pos'][section_position] + property_elem['offset']:
                #                    self.header_data['section_pos'][section_position] + property_elem['offset'] + property_elem['size']] = value_to_set

        raw_data_to_write.extend(self.section_raw_data[section_position])

        # Now creating the section 8
        # 3 subsection in section 8: The offset subsection (header), the AI and the texts

        self.section_raw_data[8] = bytearray()

        # First computing raw section (offset will be computed after)
        raw_ai_section = bytearray()
        raw_ai_offset = bytearray()

        # The offset need to take into account the different offset themselves !
        offset_value_current_ai_section = 0
        for offset in game_data.AIData.SECTION_BATTLE_SCRIPT_AI_OFFSET_LIST_DATA:
            offset_value_current_ai_section += offset['size']

        for index, section in enumerate(self.battle_script_data['ai_data']):
            if section:  # Ignoring the last section that is empty
                raw_ai_offset.extend(
                    self.__get_byte_from_int_from_game_data(offset_value_current_ai_section, game_data.AIData.SECTION_BATTLE_SCRIPT_AI_OFFSET_LIST_DATA[index]))

                section_size = 0
                for command in section:
                    section_size += command.get_size()
                    raw_ai_section.append(command.get_id())
                    raw_ai_section.extend(command.get_op_code())
                    offset_value_current_ai_section += 1 + len(command.get_op_code())
                # For reason, each AI section need to be a multiple of 4, so adding Stop till this is the case
                while section_size % 4 != 0:
                    raw_ai_section.extend([0x00])
                    offset_value_current_ai_section +=1
                    section_size +=1


        # Now analysing the text part. offset_value_current_ai_section point then to the end of AI sub-section, so the start of text offset
        raw_text_section = bytearray()
        raw_text_offset = bytearray()
        len_battle_text_sum = 0
        for battle_text in self.battle_script_data['battle_text']:
            raw_text_offset.extend(int(len_battle_text_sum).to_bytes(length=2, byteorder="little"))
            len_battle_text_sum += battle_text.get_size()
            raw_text_section.extend(battle_text.get_data_hex())

        # Now computing offset
        # Number of subsection doesn't change, neither the offset to AI-sub-section
        self.__add_section_raw_data_from_game_data(8, game_data.AIData.SECTION_BATTLE_SCRIPT_HEADER_NB_SUB)
        self.__add_section_raw_data_from_game_data(8, game_data.AIData.SECTION_BATTLE_SCRIPT_HEADER_OFFSET_AI_SUB)
        # Now adding others offset
        current_offset_section_compute = 0
        for offset_sect in game_data.AIData.SECTION_BATTLE_SCRIPT_BATTLE_SCRIPT_HEADER_LIST_DATA:
            current_offset_section_compute += offset_sect['size']

        current_offset_section_compute += len(raw_ai_offset)
        current_offset_section_compute += len(raw_ai_section)
        self.section_raw_data[8].extend(
            current_offset_section_compute.to_bytes(game_data.AIData.SECTION_BATTLE_SCRIPT_HEADER_OFFSET_TEXT_OFFSET_SUB['size'], "little"))
        current_offset_section_compute += len(raw_text_offset)
        self.section_raw_data[8].extend(
            current_offset_section_compute.to_bytes(game_data.AIData.SECTION_BATTLE_SCRIPT_HEADER_OFFSET_TEXT_SUB['size'], "little"))
        current_offset_section_compute += len(raw_text_section)

        # Now adding the data
        self.section_raw_data[8].extend(raw_ai_offset)
        self.section_raw_data[8].extend(raw_ai_section)
        self.section_raw_data[8].extend(raw_text_offset)
        self.section_raw_data[8].extend(raw_text_section)

        # And now we can add section 8 !
        raw_data_to_write.extend(self.section_raw_data[8])

        # Now writing others section
        for i in range(9, self.NUMBER_SECTION):
            raw_data_to_write.extend(self.section_raw_data[i])

        # Modifying the header section now that all sized are known
        # Modifying the section position
        header_pos_data = game_data.AIData.SECTION_HEADER_SECTION_POSITION
        file_size = 0
        for i in range(0, self.NUMBER_SECTION):
            start = header_pos_data['offset'] + i * header_pos_data['size']
            end = start + header_pos_data['size']
            file_size += len(self.section_raw_data[i])
            self.section_raw_data[0][start:end] = self.__get_byte_from_int_from_game_data(file_size, header_pos_data)

        header_file_data = game_data.AIData.SECTION_HEADER_FILE_SIZE
        self.section_raw_data[0][header_file_data['offset']:header_file_data['offset'] + header_file_data['size']] = file_size.to_bytes(
            header_pos_data['size'], header_file_data['byteorder'])
        raw_data_to_write[0:len(self.section_raw_data[0])] = self.section_raw_data[0]

        # Write back on file
        with open(dat_path, "wb") as f:
            f.write(raw_data_to_write)

    def __get_raw_data_from_game_data(self, sect_nb: int, sect_data: dict):
        sect_offset = self.header_data['section_pos'][sect_nb]
        sub_start = sect_offset + sect_data['offset']
        sub_end = sub_start + sect_data['size']
        return self.file_raw_data[sub_start:sub_end]

    def __get_byte_from_int_from_game_data(self, int_value, sect_data):
        return int_value.to_bytes(sect_data['size'], sect_data['byteorder'])

    def __add_section_raw_data_from_game_data(self, sect_nb: int, sect_data: dict, data=bytearray()):
        """If no data given, it uses the file_raw_data"""
        if len(data) == 0:
            data = self.__get_raw_data_from_game_data(sect_nb, sect_data)
        self.section_raw_data[sect_nb].extend(data)

    def __get_int_value_from_info(self, data_info, section_number=0):
        return int.from_bytes(self.__get_raw_value_from_info(data_info, section_number), data_info['byteorder'])

    def __get_raw_value_from_info(self, data_info, section_number=0):
        if section_number == 0:
            section_offset = 0
        else:
            if section_number >= len(self.header_data['section_pos']):
                return bytearray(b'')
            section_offset = self.header_data['section_pos'][section_number]
        return self.file_raw_data[section_offset + data_info['offset']:section_offset + data_info['offset'] + data_info['size']]

    def __analyze_header_section(self, game_data: GameData):
        self.header_data['nb_section'] = self.__get_int_value_from_info(game_data.AIData.SECTION_HEADER_NB_SECTION)
        sect_position = [0]  # Adding to the list the header as a section 0
        for i in range(self.header_data['nb_section']):
            sect_position.append(
                int.from_bytes(self.file_raw_data[
                               game_data.AIData.SECTION_HEADER_SECTION_POSITION['offset'] + i * game_data.AIData.SECTION_HEADER_SECTION_POSITION['size']:
                               game_data.AIData.SECTION_HEADER_SECTION_POSITION['offset'] +
                               game_data.AIData.SECTION_HEADER_SECTION_POSITION['size'] * (i + 1)],
                               game_data.AIData.SECTION_HEADER_SECTION_POSITION['byteorder']))
        self.header_data['section_pos'] = sect_position
        file_size_section_offset = 4 + self.header_data['nb_section'] * 4
        self.header_data['file_size'] = int.from_bytes(
            self.file_raw_data[file_size_section_offset:file_size_section_offset + game_data.AIData.SECTION_HEADER_FILE_SIZE['size']],
            game_data.AIData.SECTION_HEADER_FILE_SIZE['byteorder'])

    def __analyze_model_animation(self, game_data: GameData):
        #print("__analyze_model_animation")
        SECTION_NUMBER = 3

        self.model_animation_data['nb_animation'] = self.__get_int_value_from_info(game_data.AIData.SECTION_MODEL_ANIM_NB_MODEL, SECTION_NUMBER)
        list_anim_offset = []
        offset_size = game_data.AIData.SECTION_MODEL_ANIM_OFFSET['size']
        start_offset = game_data.AIData.SECTION_MODEL_ANIM_NB_MODEL['size']
        for index_offset in range(self.model_animation_data['nb_animation']):
            list_anim_offset.append(
                int.from_bytes(self.section_raw_data[SECTION_NUMBER][start_offset + index_offset * offset_size:start_offset + (index_offset + 1) * offset_size],
                               byteorder="little"))
        #print(list_anim_offset)

        animation_list = []
        start_anim = start_offset + len(list_anim_offset) * offset_size

        for index, anim_offset in enumerate(list_anim_offset):
            #print(f"Start anim: {start_anim}")
            #print(f"index: {index}, anim_offset: {anim_offset}")
            if index == len(list_anim_offset) - 1:
                end_anim = len(self.section_raw_data[SECTION_NUMBER])
            else:
                end_anim = list_anim_offset[index + 1]
            #print(f"end_anim: {end_anim}")
            animation_list.append({'nb_frame': int(self.section_raw_data[SECTION_NUMBER][start_anim]),
                                   'unk': self.section_raw_data[SECTION_NUMBER][start_anim + 1: end_anim].hex(sep=" ")})
            start_anim = end_anim
        #print(animation_list)
        #for i, el in enumerate(animation_list):
        #    print(f"Index animation: {i}, Nb frame: {el['nb_frame']}, len_animation: {len(el['unk'])}")



    def __analyze_sequence_animation(self, game_data: GameData):
        print("__analyze_sequence_animation")
        SECTION_NUMBER = 5
        print(f"Len section 5: {self.section_raw_data[SECTION_NUMBER]}")
        self.seq_animation_data['nb_anim_seq'] = self.__get_int_value_from_info(game_data.AIData.SECTION_MODEL_SEQ_ANIM_NB_SEQ, SECTION_NUMBER)
        print(f"Nb sequence: {self.seq_animation_data['nb_anim_seq']}")
        list_seq_anim_offset = []
        offset_size = game_data.AIData.SECTION_MODEL_SEQ_ANIM_OFFSET['size']
        start_offset = game_data.AIData.SECTION_MODEL_SEQ_ANIM_NB_SEQ['size']
        for index_offset in range(self.seq_animation_data['nb_anim_seq']):
            list_seq_anim_offset.append(
                int.from_bytes(self.section_raw_data[SECTION_NUMBER][start_offset + index_offset * offset_size:start_offset + (index_offset + 1) * offset_size],
                               byteorder="little"))
        print(list_seq_anim_offset)

        animation_seq_list = []
        start_anim = start_offset + len(list_seq_anim_offset) * offset_size

        for index, anim_offset in enumerate(list_seq_anim_offset):
            print(f"Start anim: {start_anim}")
            print(f"index: {index}, anim_offset: {anim_offset}")
            if index == len(list_seq_anim_offset) - 1:
                end_anim = len(self.section_raw_data[SECTION_NUMBER])
            else:
                end_anim = list_seq_anim_offset[index + 1]
            print(f"end_anim: {end_anim}")
            animation_seq_list.append({'unk': self.section_raw_data[SECTION_NUMBER][start_anim: end_anim]})
            start_anim = end_anim
        print(animation_seq_list)
        for i, el in enumerate(animation_seq_list):
            print(f"Index seq animation: {i},  seq_animation: {len(el['unk'])}")
        for i, el in enumerate(animation_seq_list):
            print(f"Seq data {i}: {el['unk'].hex(sep=" ")}")

        # Now analysing the sequence 12
        print("Analysing seq 11:")
        print(f"Seq data {11}: {animation_seq_list[11]['unk'].hex(sep=" ")}")
        sequence_analyser = SequenceAnalyser(game_data=game_data, model_anim_data=self.model_animation_data,sequence=animation_seq_list[11]['unk'])
        print("End sequence analyser")





    def __analyze_info_stat(self, game_data: GameData):
        SECTION_NUMBER = 7
        for el in game_data.AIData.SECTION_INFO_STAT_LIST_DATA:
            raw_data_selected = self.__get_raw_value_from_info(el, SECTION_NUMBER)
            data_size = len(raw_data_selected)
            if el['name'] in ['monster_name']:
                value = FF8Text(game_data=game_data, own_offset=0, data_hex=raw_data_selected, id=0)
            elif el['name'] in ([x['name'] for x in game_data.stat_data_json['stat']] + ['card', 'devour']):
                value = list(raw_data_selected)
            elif el['name'] in ['med_lvl', 'high_lvl', 'extra_xp', 'xp', 'ap', 'padding']:
                value = int.from_bytes(raw_data_selected, byteorder=el['byteorder'])
            elif el['name'] in ['low_lvl_mag', 'med_lvl_mag', 'high_lvl_mag', 'low_lvl_mug', 'med_lvl_mug', 'high_lvl_mug', 'low_lvl_drop', 'med_lvl_drop',
                                'high_lvl_drop']:  # Case with 4 values linked to 4 IDs
                list_data = list(raw_data_selected)
                value = []
                for i in range(0, data_size - 1, 2):
                    value.append({'ID': list_data[i], 'value': list_data[i + 1]})
            elif el['name'] in ['mug_rate', 'drop_rate']:  # Case with %
                value = int.from_bytes(raw_data_selected) * 100 / 255
            elif el['name'] in ['elem_def']:  # Case with elem
                value = list(raw_data_selected)
                for i in range(data_size):
                    value[i] = 900 - value[i] * 10  # Give percentage
            elif el['name'] in game_data.AIData.ABILITIES_HIGHNESS_ORDER:
                list_data = list(raw_data_selected)
                value = []
                for i in range(0, data_size - 1, 4):
                    value.append({'type': list_data[i], 'animation': list_data[i + 1], 'id': int.from_bytes(list_data[i + 2:i + 4], el['byteorder'])})
            elif el['name'] in ['status_def']:  # Case with elem
                value = list(raw_data_selected)
                for i in range(data_size):
                    value[i] = value[i] - 100  # Give percentage, 155 means immune.
            elif el['name'] in game_data.AIData.BYTE_FLAG_LIST:  # Flag in byte management
                byte_value = format((int.from_bytes(raw_data_selected)), '08b')[::-1]  # Reversing
                value = {}
                if el['name'] == 'byte_flag_0':
                    byte_list = game_data.AIData.SECTION_INFO_STAT_BYTE_FLAG_0_LIST_VALUE
                elif el['name'] == 'byte_flag_1':
                    byte_list = game_data.AIData.SECTION_INFO_STAT_BYTE_FLAG_1_LIST_VALUE
                elif el['name'] == 'byte_flag_2':
                    byte_list = game_data.AIData.SECTION_INFO_STAT_BYTE_FLAG_2_LIST_VALUE
                elif el['name'] == 'byte_flag_3':
                    byte_list = game_data.AIData.SECTION_INFO_STAT_BYTE_FLAG_3_LIST_VALUE
                else:
                    print("Unexpected byte flag {}".format(el['name']))
                    byte_list = game_data.AIData.SECTION_INFO_STAT_BYTE_FLAG_1_LIST_VALUE
                for index, bit_name in enumerate(byte_list):
                    value[bit_name] = +bool(int(byte_value[index]))
            elif el['name'] in 'renzokuken':
                value = []
                for i in range(0, el['size'], 2):  # List of 8 value of 2 bytes
                    value.append(int.from_bytes(raw_data_selected[i:i + 2], el['byteorder']))
            else:
                value = "ERROR UNEXPECTED VALUE"
                print("Unexpected name while analyzing info stat: {}".format(el['name']))

            self.info_stat_data[el['name']] = value

    def __analyze_battle_script_section(self, game_data: GameData):
        SECTION_NUMBER = 8
        if len(self.header_data['section_pos']) <= SECTION_NUMBER:
            return
        section_offset = self.header_data['section_pos'][SECTION_NUMBER]

        # Reading header
        self.battle_script_data['battle_nb_sub'] = self.__get_int_value_from_info(game_data.AIData.SECTION_BATTLE_SCRIPT_HEADER_NB_SUB, SECTION_NUMBER)
        self.battle_script_data['offset_ai_sub'] = self.__get_int_value_from_info(game_data.AIData.SECTION_BATTLE_SCRIPT_HEADER_OFFSET_AI_SUB, SECTION_NUMBER)
        self.battle_script_data['offset_text_offset'] = self.__get_int_value_from_info(game_data.AIData.SECTION_BATTLE_SCRIPT_HEADER_OFFSET_TEXT_OFFSET_SUB,
                                                                                       SECTION_NUMBER)
        self.battle_script_data['offset_text_sub'] = self.__get_int_value_from_info(game_data.AIData.SECTION_BATTLE_SCRIPT_HEADER_OFFSET_TEXT_SUB,
                                                                                    SECTION_NUMBER)

        # Reading text offset subsection
        nb_text = self.battle_script_data['offset_text_sub'] - self.battle_script_data['offset_text_offset']
        for i in range(0, nb_text, game_data.AIData.SECTION_BATTLE_SCRIPT_TEXT_OFFSET['size']):
            start_data = section_offset + self.battle_script_data['offset_text_offset'] + i
            end_data = start_data + game_data.AIData.SECTION_BATTLE_SCRIPT_TEXT_OFFSET['size']
            text_list_raw_data = self.file_raw_data[start_data:end_data]
            # if i > 0 and text_list_raw_data == b'\x00\x00':  # Weird case where there is several pointer by the diff but several are 0 (which point to the same value)
            #    break
            self.battle_script_data['text_offset'].append(
                int.from_bytes(text_list_raw_data, byteorder=game_data.AIData.SECTION_BATTLE_SCRIPT_HEADER_OFFSET_TEXT_OFFSET_SUB['byteorder']))
        # Reading text sub-section
        for text_pointer in self.battle_script_data['text_offset']:  # Reading each text from the text offset
            combat_text_raw_data = bytearray()
            for i in range(self.MAX_MONSTER_SIZE_TXT_IN_BATTLE):  # Reading char by char to search for the 0
                char_index = section_offset + self.battle_script_data['offset_text_sub'] + text_pointer + i
                if char_index >= len(self.file_raw_data):  # Shouldn't happen, only on garbage data / self.header_data['file_size'] can be used
                    pass
                else:
                    raw_value = self.file_raw_data[char_index]
                    if raw_value != 0:
                        combat_text_raw_data.extend(int.to_bytes(raw_value))
                    else:
                        break
            if combat_text_raw_data:
                self.battle_script_data['battle_text'].append(FF8Text(game_data=game_data, own_offset=0, data_hex=combat_text_raw_data, id=0))
            else:
                self.battle_script_data['battle_text'] = []

        # Reading AI subsection

        ## Reading offset
        ai_offset = section_offset + self.battle_script_data['offset_ai_sub']
        for offset_param in game_data.AIData.SECTION_BATTLE_SCRIPT_AI_OFFSET_LIST_DATA:
            start_data = ai_offset + offset_param['offset']
            end_data = ai_offset + offset_param['offset'] + offset_param['size']
            self.battle_script_data[offset_param['name']] = int.from_bytes(self.file_raw_data[start_data:end_data], offset_param['byteorder'])

        start_data = ai_offset + self.battle_script_data['offset_init_code']
        end_data = ai_offset + self.battle_script_data['offset_ennemy_turn']
        init_code = list(self.file_raw_data[start_data:end_data])
        start_data = ai_offset + self.battle_script_data['offset_ennemy_turn']
        end_data = ai_offset + self.battle_script_data['offset_counterattack']
        ennemy_turn_code = list(self.file_raw_data[start_data:end_data])
        start_data = ai_offset + self.battle_script_data['offset_counterattack']
        end_data = ai_offset + self.battle_script_data['offset_death']
        counterattack_code = list(self.file_raw_data[start_data:end_data])
        start_data = ai_offset + self.battle_script_data['offset_death']
        end_data = ai_offset + self.battle_script_data['offset_before_dying_or_hit']
        death_code = list(self.file_raw_data[start_data:end_data])
        start_data = ai_offset + self.battle_script_data['offset_before_dying_or_hit']
        end_data = section_offset + self.battle_script_data['offset_text_offset']
        before_dying_or_hit_code = list(self.file_raw_data[start_data:end_data])
        list_code = [init_code, ennemy_turn_code, counterattack_code, death_code, before_dying_or_hit_code]
        self.battle_script_data['ai_data'] = []
        for index, code in enumerate(list_code):
            index_read = 0
            list_result = []
            while index_read < len(code):
                all_op_code_info = game_data.ai_data_json["op_code_info"]
                op_code_ref = [x for x in all_op_code_info if x["op_code"] == code[index_read]]
                if not op_code_ref and code[index_read] >= 0x40:
                    index_read += 1
                    continue
                elif op_code_ref:  # >0x40 not used
                    op_code_ref = op_code_ref[0]
                    start_param = index_read + 1
                    end_param = index_read + 1 + op_code_ref['size']
                    if list_result:
                        previous_command = list_result[-1]
                    else:
                        previous_command = None
                    command = CommandAnalyser(code[index_read], code[start_param:end_param], game_data=game_data,
                                              battle_text=self.battle_script_data['battle_text'],
                                              info_stat_data=self.info_stat_data, color=game_data.AIData.COLOR, previous_command=previous_command)
                    list_result.append(command)
                    index_read += 1 + op_code_ref['size']
            self.battle_script_data['ai_data'].append(list_result)
        self.battle_script_data['ai_data'].append([])  # Adding a end section that is empty to mark the end of the all IA section

    def insert_command(self, code_section_id: int, command: CommandAnalyser, index_insertion: int = 0):
        self.battle_script_data['ai_data'][code_section_id].insert(index_insertion, command)

    def remove_command(self, code_section_id: int, index_removal: int = 0):
        del self.battle_script_data['ai_data'][code_section_id][index_removal]

    def __remove_stop_end(self, list_result):
        id_remove = 0
        for i in range(len(list_result)):
            if list_result[i]['id'] == 0x00:  # STOP
                if i + 1 < len(list_result):
                    if list_result[i + 1]['id'] == 0x00:
                        id_remove = i + 1
                        break
        return list_result[:id_remove or None]

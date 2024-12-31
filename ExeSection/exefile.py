from FF8GameData.GenericSection.offsetandtext import SectionOffsetAndText
from FF8GameData.GenericSection.section import Section
from FF8GameData.GenericSection.sizeandoffsetandtext import SectionSizeAndOffsetAndText
from FF8GameData.gamedata import GameData, LangType, MsdType, RemasterCardType


class SectionExeFile(Section):
    OFFSET_SIZE = 2
    GENERAL_OFFSET = 0x400000

    def __init__(self, game_data: GameData, data_hex):
        Section.__init__(self, game_data=game_data, data_hex=data_hex, id=0, own_offset=0, name=".Exe")
        self._section_list = []
        if not self._game_data.exe_data_json:
            self._game_data.load_exe_data()
        self._lang = LangType.ENGLISH
        self.__analyse_data()

    def __str__(self):
        return str("To be define")

    def __repr__(self):
        return self.__str__()

    def produce_msd(self, msd_type: MsdType):
        msd_offset_size = 4
        msd_data = bytearray()
        if msd_type == MsdType.CARD_NAME:
            id = 3
        elif msd_type == MsdType.SCAN_TEXT:
            id = 4
        else:
            print("Unknown msd type")
            id = 4
        index = [i for i in range(len(self._section_list)) if self._section_list[i].id == id][0]
        self._section_list[index].update_data_hex()
        offset_list = self._section_list[index].get_offset_section().get_all_offset()
        text_list = self._section_list[index].get_text_section().get_text_list()
        if len(text_list) != len(offset_list):
            print(f"Unexpected diff size between offset list (size:{len(offset_list)}) and text list (size:{len(text_list)})")
        first_offset = offset_list[0]
        # As the offset from .exe vary from the one use in msd, shift them !
        for i in range(len(offset_list)):
            # First remove the original offset
            offset_list[i] -= first_offset
            # Then add the start of the first one for msd
            offset_list[i] += len(offset_list) * msd_offset_size
            msd_data.extend(offset_list[i].to_bytes(length=msd_offset_size, byteorder="little"))
        msd_data.extend(self._section_list[index].get_text_section().get_data_hex())
        return msd_data

    def produce_remaster_file(self, remaster_type:RemasterCardType):
        if remaster_type == RemasterCardType.CARD_NAME:
            return self._section_list[3].get_data_hex()
        else:
            return self._section_list[3].get_data_hex()

    def produce_str_hext(self, card_name=False):
        """Deprecated and bugged, msd is better for text"""
        hext_str = "# File produced by ShumiTranslator or CC-Group tool, made by HobbitDur\n"
        hext_str += "# You can support HobbitDur on Patreon: https://www.patreon.com/HobbitMods\n\n"
        # First writing base data (not sure why necessary, but everyone does it)
        hext_str += "#Base writing (not sure why necessary)\n"
        hext_str += "600000:1000\n\n"
        # Then adding the offset of the data
        hext_str += "#Offset to dynamic data\n"
        hext_str += "+{:X}\n\n".format(self.GENERAL_OFFSET)

        card_name_start = self._game_data.card_data_json["card_data_offset"]["eng_name_section_start"] + 2
        if card_name:
            hext_str += "#Card name start at {:X}, so we just move the pointer of 0x{:X}+0x{:X}=0x{:X}\n".format(card_name_start,
                                                                                                                 self.GENERAL_OFFSET,
                                                                                                                 card_name_start,
                                                                                                                 self.GENERAL_OFFSET + card_name_start)
            hext_str += "+{:X}\n\n".format(self.GENERAL_OFFSET + card_name_start)
            text_section = self._section_list[3].get_text_section()
            for index_card, card_text in enumerate(text_section.get_text_list()):
                hext_str += f"#Changing name of card from {self._game_data.card_data_json["card_info"][index_card]["name"]} to {card_text.get_str()}\n"
                hext_str += "{:X} = ".format(index_card * self.OFFSET_SIZE)
                hext_str += "{}\n".format(card_text.get_data_hex().hex(sep=" "))
        return hext_str

    # TODO Change the index 3 by a value in a json file
    def get_section_card_name(self) -> SectionSizeAndOffsetAndText:
        return self._section_list[3]

    # TODO Change the index 4 by a value in a json file
    def get_section_scan_text(self) -> SectionOffsetAndText:
        return self._section_list[4]

    def get_lang(self):
        return self._lang

    def update_data_hex(self):
        for section in self._section_list:
            section.update_data_hex()

    def __analyse_data(self):
        self.__analyse_lang()
        nb_card = len(self._game_data.card_data_json["card_info"])
        card_data_size = self._game_data.exe_data_json["card_data_offset"]["card_data_size"]

        menu_offset = self._game_data.exe_data_json["card_data_offset"]["eng_menu"]
        menu_offset += self.__get_lang_card_offset()

        #1st section
        self._section_list.append(
            Section(self._game_data, self._data_hex[0:menu_offset], id=0, own_offset=0, name="Ignored start data"))

        #2nd section
        next_offset = menu_offset + nb_card * card_data_size
        self._section_list.append(
            Section(self._game_data, self._data_hex[menu_offset:next_offset], id=1, own_offset=0, name="Card menu data"))

        #3rd section
        offset = next_offset
        card_generic_text_offset = self._game_data.exe_data_json["card_data_offset"]["eng_card_generic_text_start"]
        card_generic_text_offset += self.__get_lang_card_offset()
        self._section_list.append(
            Section(self._game_data, self._data_hex[offset:card_generic_text_offset], id=2, own_offset=0, name="Ignored data"))


        #4rd section
        next_offset = None
        self._section_list.append(
            Section(self._game_data, self._data_hex[card_generic_text_offset:card_generic_text_offset], id=2, own_offset=0, name="Ignored data"))


        name_offset = self._game_data.exe_data_json["card_data_offset"][
                          "eng_name_section_start"] + self.__get_lang_card_offset()
        self._section_list.append(
            Section(self._game_data, self._data_hex[next_offset:name_offset], id=2, own_offset=0,
                    name="Ignored after card data"))
        card_name_section = SectionSizeAndOffsetAndText(self._game_data, self._data_hex[name_offset:], id=3,
                                                        own_offset=name_offset, name="Card name", offset_size=2,
                                                        ignore_empty_offset=False)
        card_name_section.update_data_hex()
        self._section_list.append(card_name_section)

        scan_offset_start = self._game_data.exe_data_json["scan_data_offset"]["eng_section_start"] + self.__get_lang_scan_offset()
        scan_nb_offset = self._game_data.exe_data_json["scan_data_offset"]["nb_offset"]
        scan_offset_size = self._game_data.exe_data_json["scan_data_offset"]["offset_size"]
        scan_section = SectionOffsetAndText(self._game_data, self._data_hex[scan_offset_start:], id=4,
                                            own_offset=name_offset, name="Scan text", offset_size=scan_offset_size, nb_offset=scan_nb_offset,
                                            ignore_empty_offset=False, nb_byte_shift=0, text_offset_start_0=True)
        scan_section.update_data_hex()
        self._section_list.append(scan_section)

        self._section_list.append(Section(self._game_data, self._data_hex[name_offset + len(card_name_section):], id=5,
                                          own_offset=name_offset + len(card_name_section), name="Ignored end data"))

    def __analyse_lang(self):
        if self._data_hex[self._game_data.exe_data_json["lang"]["offset"]] == self._game_data.exe_data_json["lang"]["english_value"]:
            self._lang = LangType.ENGLISH
        elif self._data_hex[self._game_data.exe_data_json["lang"]["offset"]] == self._game_data.exe_data_json["lang"]["french_value"]:
            self._lang = LangType.FRENCH
        elif self._data_hex[self._game_data.exe_data_json["lang"]["offset"]] == self._game_data.exe_data_json["lang"]["german_value"]:
            self._lang = LangType.GERMAN
        elif self._data_hex[self._game_data.exe_data_json["lang"]["offset"]] == self._game_data.exe_data_json["lang"]["spanish_value"]:
            self._lang = LangType.SPANISH
        elif self._data_hex[self._game_data.exe_data_json["lang"]["offset"]] == self._game_data.exe_data_json["lang"]["italian_value"]:
            self._lang = LangType.ITALIAN
        else:
            print(f"Unexpected language, value: {self._data_hex[self._game_data.exe_data_json["lang"]["offset"]]}")
            self._lang = LangType.ENGLISH

    def __get_lang_card_offset(self):
        if self._lang == LangType.ENGLISH:
            return 0
        elif self._lang == LangType.FRENCH:
            return self._game_data.exe_data_json["card_data_offset"]["fr_offset"]
        elif self._lang == LangType.ITALIAN:
            return self._game_data.exe_data_json["card_data_offset"]["it_offset"]
        elif self._lang == LangType.GERMAN:
            return self._game_data.exe_data_json["card_data_offset"]["de_offset"]
        elif self._lang == LangType.SPANISH:
            return self._game_data.exe_data_json["card_data_offset"]["es_offset"]
        else:
            print("Unknown Language")
            return 0

    def __get_lang_scan_offset(self):
        if self._lang == LangType.ENGLISH:
            return 0
        elif self._lang == LangType.FRENCH:
            return self._game_data.exe_data_json["scan_data_offset"]["fr_offset"]
        elif self._lang == LangType.ITALIAN:
            return self._game_data.exe_data_json["scan_data_offset"]["it_offset"]
        elif self._lang == LangType.GERMAN:
            return self._game_data.exe_data_json["scan_data_offset"]["de_offset"]
        elif self._lang == LangType.SPANISH:
            return self._game_data.exe_data_json["scan_data_offset"]["es_offset"]
        else:
            print("Unknown Language")
            return 0

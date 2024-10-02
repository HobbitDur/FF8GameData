import os

from FF8GameData.FF8HexReader.mngrphd import MngrphdEntry, Mngrphd
from FF8GameData.FF8HexReader.section import Section
from FF8GameData.gamedata import GameData, SectionType


class Mngrp(Section):
    def __init__(self, game_data: GameData, data_hex: bytearray, header_entry_list: [MngrphdEntry] = ()):
        Section.__init__(self, game_data=game_data, data_hex=data_hex, id=0, own_offset=0, name="mngrp")
        self._section_list = []
        self._game_data.load_mngrp_data()
        # If not entry list given, use the default one
        if not header_entry_list:
            for index_section, section in enumerate(self._game_data.mngrp_data_json()['sections']):
                if index_section == len(self._game_data.mngrp_data_json()['sections']) - 1:
                    end_section = len(self._data_hex)
                else:
                    end_section = self._game_data.mngrp_data_json()['sections'][index_section + 1]['section_offset']
                section_hex = self._data_hex[section['section_offset']:end_section]
                new_section = Section(game_data=self._game_data, data_hex=section_hex, id=index_section,
                                      own_offset=section["section_offset"], name=section["section_name"])
                self._section_list.append(new_section)
        else:
            current_id_section = 0
            for index_section, entry in enumerate(header_entry_list):
                section_hex = self._data_hex[entry.seek: entry.seek + entry.size]
                if entry.invalid_value:
                    id_section = -1
                    offset = entry.seek
                else:
                    id_section = current_id_section
                    offset = entry.seek + 1
                    current_id_section += 1
                new_section = Section(game_data=self._game_data, data_hex=section_hex, id=id_section,
                                      own_offset=offset, name="")
                self._section_list.append(new_section)


    def __str__(self):
        return_str = ""
        for i, section in enumerate(self._section_list):
            return_str += f"Section mngrp n°{i}(id={section.id}, offset={section.own_offset}, len={section.get_size()})" + "\n"
        return return_str

    def __repr__(self):
        return self.__str__()

    def get_section_list(self):
        return self._section_list

    def get_section_by_id(self, section_id):
        return self._section_list[section_id]

    def set_section_by_id_and_bytearray(self, section_id: int, data_section_hex: bytearray, mngrphd: Mngrphd):
        print("set_section_by_id")
        local_index_section = 0
        for i, section in enumerate(self._section_list):
            if section.id == section_id:
                local_index_section = i
                break
        print(f"local_index_section: {local_index_section}")



        own_offset_start = self._section_list[local_index_section].own_offset
        len_old = len(self._section_list[local_index_section])
        name = self._section_list[local_index_section].name
        new_section = Section(game_data=self._game_data, data_hex=data_section_hex, id=local_index_section,
                              own_offset=own_offset_start, name=name)
        new_section.fill_256()
        self._section_list[local_index_section] = new_section
        self.__shift_offset(len_old=len_old, mngrphd=mngrphd, section_id=local_index_section, new_section=new_section)

    def set_section_by_id(self, section_id: int, new_section: Section, mngrphd: Mngrphd):
        local_index_section = 0
        for i, section in enumerate(self._section_list):
            if section.id == section_id:
                local_index_section = i
                break

        len_old = len(self._section_list[local_index_section])
        new_section.fill_256()
        self._section_list[local_index_section] = new_section
        self.__shift_offset(len_old=len_old, mngrphd=mngrphd, section_id=local_index_section, new_section=new_section)

    def __shift_offset(self, len_old: int, mngrphd: Mngrphd, section_id, new_section):
        print(f"len_old: {len_old}")
        print(f"section_id: {section_id}")
        print(f"new_section: {new_section}")
        print(f"len(new_section): {len(new_section)}")
        if not mngrphd.get_entry_list()[section_id].invalid_value:
            own_offset_diff = len(new_section) - len_old
            for i in range(section_id + 1, len(self._section_list)):
                if not mngrphd.get_entry_list()[i].invalid_value:
                    self._section_list[i].own_offset += own_offset_diff
            mngrphd.update_from_section_list(self._section_list)

    def update_data_hex(self):
        self._data_hex = bytearray()
        for section in self._section_list:
            #if section.type == SectionType.TKMNMES:
            section.update_data_hex()
            self._data_hex.extend(section.get_data_hex())
        self._size = len(self._data_hex)


if __name__ == "__main__":
    game_data = GameData(os.path.join("..", "..", "FF8GameData"))
    file_mngrphd_in = "mngrphd.bin"
    file_mngrphd_data = bytearray()
    with open(file_mngrphd_in, "rb") as file:
        file_mngrphd_data.extend(file.read())
    mngprhd_section = Mngrphd(game_data, file_mngrphd_data)

    entry_list_valid = mngprhd_section.get_valid_entry_list()
    entry_list = mngprhd_section.get_entry_list()
    file_mngrp_in = "mngrp.bin"
    file_mngrp_data = bytearray()
    with open(file_mngrp_in, "rb") as file:
        file_mngrp_data.extend(file.read())
    mngrp_section_valid = Mngrp(game_data=game_data, data_hex=file_mngrp_data, header_entry_list=entry_list_valid)
    mngrp_section = Mngrp(game_data=game_data, data_hex=file_mngrp_data, header_entry_list=entry_list)

    file_mngrp_out = "mngrp_out.bin"
    with open(file_mngrp_out, "wb") as file:
        file.write(mngrp_section.get_data_hex())

    # mngrp_section_valid.set_section_by_id(0, bytearray([0x60, 0x02, 0x00]), mngprhd_section )

    file_mngrp_out = "mngrp_valid_out.bin"
    with open(file_mngrp_out, "wb") as file:
        file.write(mngrp_section_valid.get_data_hex())

    file_mngrphd_out = "mngrphd_out.bin"
    with open(file_mngrphd_out, "wb") as file:
        file.write(mngprhd_section.get_data_hex())

from ..gamedata import GameData


class SequenceAnalyser:

    def __init__(self, game_data: GameData, model_anim_data, sequence: bytearray):
        self._sequence = sequence
        self._model_anim_data = model_anim_data
        self.game_data = game_data
        self.__op_id = 0
        self.__op_code = []
        self.__raw_parameters = []
        self.__raw_text = ""
        self.__analyse_sequence()

    def __str__(self):
        return f"ID: {self.__op_id}, op_code: {self.__op_code}"

    def __repr__(self):
        return self.__str__()

    def __analyse_sequence(self):
        all_op_info = self.game_data.anim_sequence_data_json['op_code_info']
        op_code = []
        index_data = 0
        text_analyze = ""
        while index_data < len(self._sequence):
            hex_data = self._sequence[index_data]
            current_opcode_int = int.from_bytes(hex_data)
            current_opcode_hex_str = "0x" + (hex_data.hex()).upper()
            text_analyze += f"{(hex_data.hex(" ")).upper()} "
            current_op_code_data = [x for x in self.game_data.anim_sequence_data_json["op_code_info"] if int(x['opcode'], 16) == current_opcode_int]
            if current_op_code_data:
                current_op_code_data = current_op_code_data[0]
            else:
                print(f"Opcode {current_opcode_int} not found, assuming 0 param")
                text_analyze += ": Unknown"
                continue

            # Reading param
            if current_op_code_data["size"] == -1:
                current_op_code_size = 1
            else:
                current_op_code_size = current_op_code_data["size"]
            nb_param_analyzed = 0
            param_list = []
            while True:
                if nb_param_analyzed == current_op_code_size:# If we analyzed all param
                    break
                index_data += 1
                current_param = self._sequence[index_data]
                param_list.append(current_param)
                current_param_int = int.from_bytes(current_param)
                text_analyze +=  f"{(current_param.hex(" ")).upper()} "
                nb_param_analyzed += 1
                if current_opcode_int in [0x99, 0xB1]: #Last one is FF
                    if current_param_int != 0xFF:
                        current_op_code_size +=1
                    else:
                        break
                if current_opcode_int == 0xB0:
                    print("Todo !")
                    break
                if current_opcode_int == 0xB8:
                    print("Todo !")
                    break
            text_analyze += ": "

            # Now analyzing the opcode
            if current_opcode_int < 0x80:
                text_analyze += f"Play anim {current_opcode_hex_str}"
            else:
                # Searching the data in op code list
                description_param = []
                if current_op_code_data['complexity'] == "simple":
                    for index_param_in_str, param_type in enumerate(current_op_code_data['param_type']):
                        param_index = current_op_code_data['param_index'][index_param_in_str]
                        param_data = param_list[param_index]
                        description = current_op_code_data['text']
                        # For the moment we mainly show int, but in the futur we will show text linked to this ID
                        if param_type == "anim_id":
                            description_param.append(f"{int.from_bytes(param_data, byteorder="little", signed=False )}")
                        elif param_type == "effect_id":
                            description_param.append(f"{int.from_bytes(param_data, byteorder="little", signed=False )}")
                        elif param_type == "fade_effect_id":
                            description_param.append(f"{int.from_bytes(param_data, byteorder="little", signed=False )}")
                        elif param_type == "ubyte":
                            description_param.append(f"{int.from_bytes(param_data, byteorder="little", signed=False )}")
                        elif param_type == "sbyte":
                            description_param.append( f"{int.from_bytes(param_data, byteorder="little", signed=True )}")
                        elif param_type == "int16":
                            description_param.append( f"{int.from_bytes(param_list[param_index: param_index+1], byteorder="little", signed=True )}")
                        else:
                            description_param.append( "Unknown type parameter")
                    text_analyze += current_op_code_data['text'].format(*description_param)
                elif current_op_code_data['complexity'] == "complex":
                    if current_op_code_data['op_code'] in ["0x99", "0xb1"]:
                        pass
                    if int(current_op_code_data['op_code'], 16) in [0xC3, 0xC7, 0xCB, 0xCF, 0xD3, 0xD7, 0xDB, 0xDF, 0xE3, 0xE5]:
                        if param_list[0] < 0x80:
                            special_read = [x for x in self.game_data.anim_sequence_data_json["special_change_current_value_params"] if  int.from_bytes(param_list[0]) == x['param_id']]
                            if special_read:
                                special_read = special_read[0]
                            else:
                                print(f"No param_id in special_change_current_value_params for {param_list[0]}")
                            description_param.append(special_read)
                            text_analyze += current_op_code_data['text'].format(description_param)
                        else:
                            if current_op_code_data['op_code'] == "0xE5":
                                special_read = [x for x in self.game_data.anim_sequence_data_json["e5_special_params"] if "0x80" == x['param_id']]
                            else:
                                special_read = [x for x in self.game_data.anim_sequence_data_json["special_change_current_value_params"] if
                                                "0x80" == x['param_id']]
                            if special_read:
                                special_read = special_read[0]
                            else:
                                print(f"No param_id in special_change_current_value_params for >=0x80 values")
                            text_analyze += current_op_code_data['text'].format(special_read.format(param_list[0]))


            text_analyze += "\n"
        print("End __analyse_sequence")

    def get_size(self):
        return len(self._sequence)

    def get_id(self):
        return self.__op_id

    def get_op_code(self):
        return self.__op_code

    def get_text_param(self):
        return self.__raw_parameters

    def get_text(self):
        return True

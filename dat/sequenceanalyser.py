from ..gamedata import GameData


class SequenceAnalyser:

    def __init__(self, game_data: GameData, model_anim_data,sequence: bytearray):
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
        while index_data < len(self._sequence):
            hex_data = self._sequence[index_data]

            if hex_data < self._model_anim_data['nb_animation']:
                print("Op id {:02X}  means play anim {}".format(hex_data, hex_data))
                index_data+=1
            else:
                # Searching the data in op code list

                op_info = [x for x in all_op_info if x['op_code'] == hex_data]
                if op_info:
                    op_info = op_info[0]
                else:
                    print("op code {:02X} not found".format(hex_data))
                    index_data += 1
                    continue
                    op_info = {"op_code": 0x00, "size": 0, "text": "Unknown", "param_index": [], "complexity": "simple", "param_type": [], "param_list": []}
                if op_info['complexity'] == "simple":
                    op_code = self._sequence[index_data+1: index_data + op_info['size']+1]
                    op_code_text_param = []
                    for index_param, param_type in enumerate(op_info['param_type']):
                        # For the moment we mainly show int, but in the futur we will show text linked to this ID
                        param_index = op_info['param_index'][index_param]
                        param_data = op_code[param_index]
                        if param_type == "anim_id":
                            op_code_text_param.append(int(param_data))
                        if param_type == "seq_id":
                            op_code_text_param.append(int(param_data))
                        if param_type == "effect_id":
                            op_code_text_param.append(
                                int.from_bytes(bytes([op_code[param_index], op_code[param_index+1]]), byteorder="little"))
                        if param_type == "start_anim_id":
                            op_code_text_param.append(
                                int.from_bytes(bytes([op_code[param_index], op_code[param_index+1]]), byteorder="little"))
                        if param_type == "local_sound_id":
                            op_code_text_param.append(
                                int.from_bytes(bytes([op_code[param_index], op_code[param_index+1]]), byteorder="little"))
                        if param_type == "general_sound_id":
                            op_code_text_param.append(
                                int.from_bytes(bytes([op_code[param_index], op_code[param_index+1]]), byteorder="little"))
                        if param_type == "aura_id":
                            print("arua")
                            op_code_text_param.append(
                                int.from_bytes(bytes([op_code[param_index], op_code[param_index+1]]), byteorder="little"))
                        if param_type == "visibility":
                            if param_data == 0x02:
                                op_code_text_param.append("Hide")
                            elif param_data == 0x03:
                                op_code_text_param.append("Show")
                            else:
                                op_code_text_param.append("Unknown_visibility")
                    op_code_text = op_info['text']
                    if op_code_text_param:
                        op_code_text = op_code_text.format(*op_code_text_param)
                    print("Op id {:02X} with Op code {} means {}".format(op_info['op_code'], ' '.join("{:02X}".format(byte) for byte in op_code), op_code_text))
                    index_data += op_info['size']+1
                elif op_info['complexity'] == "complex":
                    added_text = ""
                    if op_info['op_code'] == 0xc1:
                        if self._sequence[index_data + 1] == 0x00 and self._sequence[index_data + 2] == 0xe5 and self._sequence[index_data + 3] == 0x0f:
                            added_text = "Place model at home location"
                            op_code = self._sequence[index_data: index_data + 3]
                            index_data += 3
                        elif self._sequence[index_data + 2] == 0xe5 and self._sequence[index_data + 3] == 0x7f:
                            anim = self._sequence[index_data + 4]
                            nb_loop = self._sequence[index_data + 1]
                            added_text = "Loop {:02X} times anim {:02X}".format(nb_loop, anim)
                            op_code = self._sequence[index_data: index_data + 4]
                            index_data += 4
                        else:
                            added_text = "Unknown C1"
                            index_data += 1
                            op_code = None
                    elif op_info['op_code'] == 0xc3:
                        if self._sequence[index_data + 1] == 0x7F:
                            added_text = "Wait till previous sequence is complete"
                            op_code = self._sequence[index_data: index_data + 7]
                            index_data += 7
                        elif self._sequence[index_data + 1] == 0x0C:
                            added_text = "Unknown but size found"
                            op_code = self._sequence[index_data: index_data + 6]
                            index_data += 6
                        elif self._sequence[index_data + 1] == 0x08:
                            added_text = "Unknown but size found"
                            op_code = self._sequence[index_data: index_data + 6]
                            index_data += 6
                        else:
                            added_text = "Unknown C3"
                            index_data += 1
                            op_code = None
                    if op_code:
                        op_code_text = ' '.join("{:02X}".format(byte) for byte in op_code)
                    else:
                        op_code_text = "None"
                    print("Op code {:02X} with Op code {} means {}".format(op_info['op_code'], op_code_text, added_text))


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
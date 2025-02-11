from html import escape
from idlelib.undo import Command

from ..gamedata import GameData


class CommandAnalyser:
    PARAM_CHAR_LEFT = "["
    PARAM_CHAR_RIGHT = "]"

    def __init__(self, op_id: int, op_code: list, game_data: GameData, battle_text=(), info_stat_data={},
                 line_index=0, color="#0055ff", text_param=False, previous_command=None):
        self.__op_id = op_id
        self.__op_code = op_code
        self.__battle_text = battle_text
        self.__text_colored = ""
        self.game_data = game_data
        self.info_stat_data = info_stat_data
        self.__color_param = color
        self.line_index = line_index
        self.__if_index = 0
        self.was_physical = False
        self.was_magic = False
        self.was_item = False
        self.was_gforce = False
        self.type_data = []
        self.id_possible_list = [{'id': x['op_code'], 'data': x['short_text']} for x in self.game_data.ai_data_json['op_code_info']]
        self.param_possible_list = []
        self.__size = 0
        self.__raw_text = ""
        self.__raw_parameters = []
        self.__raw_text_added = []
        self.previous_command = previous_command
        if text_param:
            self.__analyse_op_data_with_text_param()
        else:
            self.__analyse_op_data()

    def __str__(self):
        return f"Command(ID: {self.__op_id}, op_code: {self.__op_code}, text: {self.get_text()})"

    def __repr__(self):
        return self.__str__()

    def reset_data(self):
        self.was_physical = False
        self.was_magic = False
        self.was_item = False
        self.was_gforce = False
        self.param_possible_list = []
        self.__if_index = 0
        self.type_data = []
        self.__size = 0
        self.__raw_text = ""
        self.__raw_parameters = []
        self.__raw_text_added = []

    def get_size(self):
        return self.__size

    def set_color(self, color):
        self.__color_param = color
        self.__analyse_op_data()

    def set_op_id(self, op_id):
        self.reset_data()
        self.__op_id = op_id
        op_info = self.__get_op_code_line_info()
        self.__op_code = [0] * op_info["size"]

        self.id_possible_list = [{'id': x['op_code'], 'data': x['short_text']} for x in self.game_data.ai_data_json['op_code_info']]
        self.__analyse_op_data()

    def set_op_code(self, op_code):
        self.reset_data()
        self.__op_code = op_code
        self.__analyse_op_data()

    def get_id(self):
        return self.__op_id

    def get_op_code(self):
        return self.__op_code

    def get_text_param(self):
        return self.__raw_parameters

    def get_text(self, with_size=True, raw=False, for_code=False, html=False):
        text = self.__raw_text
        parameters = self.__raw_parameters.copy()

        if for_code:
            parameters = []
            for parameter in self.__raw_parameters:
                parameters.append(self.PARAM_CHAR_LEFT + str(parameter) + self.PARAM_CHAR_RIGHT)

        if html:
            if for_code:
                list_comparator_destination = self.game_data.ai_data_json['list_comparator_ifritAI_html']
            else:
                list_comparator_destination = self.game_data.ai_data_json['list_comparator_html']
            for i in range(len(list_comparator_destination)):
                text = text.replace(self.game_data.ai_data_json['list_comparator'][i], list_comparator_destination[i])
                for j in range(len(parameters)):
                    parameters[j] = str(parameters[j]).replace(self.game_data.ai_data_json['list_comparator'][i],
                                                               list_comparator_destination[i])
            for i in range(len(parameters)):
                parameters[i] = '<span style="color:' + self.__color_param + ';">' + parameters[i] + '</span>'

        for i in range(len(parameters)):  # Adding special text computation
            for text_added in self.__raw_text_added:
                if text_added['id'] == i:
                    if html:
                        parameters[i] = parameters[i] + text_added['text_html']
                    else:
                        parameters[i] = parameters[i] + text_added['text']
        if not raw:
            text = text.format(*parameters)
        if with_size:
            text += " (size:{}bytes)".format(self.__size)
        # Removing return line as we compute line by line
        if for_code:
            text = text.replace('<br/>', '')
            text = text.replace('<br>', '')

        return text

    def set_if_index(self, if_index):
        self.__if_index = if_index

    def __get_op_code_line_info(self):
        all_op_code_info = self.game_data.ai_data_json["op_code_info"]
        op_research = [x for x in all_op_code_info if x["op_code"] == self.__op_id]
        if op_research:
            op_research = op_research[0]
        else:
            print("No op_code defined for op_id: {}".format(self.__op_id))
            op_research = [x for x in all_op_code_info if x["op_code"] == 255][0]
        return op_research

    def __analyse_op_data_with_text_param(self):
        op_code_list = self.get_op_code()
        op_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x["op_code"] == self.get_id()]
        if op_info:
            op_info = op_info[0]
        else:
            print(f"Didn't find op id: {self.get_id()}, assuming stop")
            op_info = self.game_data.ai_data_json['op_code_info'][0]

        # Analysing simple cases by transforming the text into an integer
        if op_info['complexity'] == "simple":
            # Putting the parameters type in the correct order
            param_type_sorted = op_info['param_type'].copy()
            for i, param_index in enumerate(op_info['param_index']):
                param_type_sorted[param_index] = op_info['param_type'][i]
            for i, param_type in enumerate(param_type_sorted):
                if param_type == "int":
                    op_code_list[i] = int(op_code_list[i])
                elif param_type == "int_shift":
                    shift = op_info['param_list'][0]
                    op_code_list[i] = int(op_code_list[i]) - shift
                elif param_type == "percent":
                    op_code_list[i] = int(int(op_code_list[i]) / 10)
                elif param_type == "var":
                    op_code_list[i] = [x['op_code'] for x in self.game_data.ai_data_json['list_var'] if x['var_name'] == op_code_list[i]][0]
                elif param_type == "activate":
                    op_code_list[i] = [x['id'] for x in self.game_data.ai_data_json['activate_type'] if x['name'] == op_code_list[i]][0]
                elif param_type == "special_action":
                    op_code_list[i] = [x['id'] for x in self.game_data.special_action_data_json['special_action'] if x['name'] == op_code_list[i]][0]
                elif param_type == "monster_line_ability":
                    op_code_list[i] = int(op_code_list[i])
                elif param_type == "ability":
                    op_code_list[i] = [x['id'] for x in self.game_data.enemy_abilities_data_json['abilities'] if x['name'] == op_code_list[i]][0]
                elif param_type == "card":
                    op_code_list[i] = [x['id'] for x in self.game_data.card_data_json['card_info'] if x['name'] == op_code_list[i]][0]
                elif param_type == "monster":
                    op_code_list[i] = [x['id'] for x in self.game_data.monster_data_json['monster'] if x['name'] == op_code_list[i]][0]
                elif param_type == "item":
                    op_code_list[i] = [x['id'] for x in self.game_data.item_data_json['items'] if x['name'] == op_code_list[i]][0]
                elif param_type == "gforce":
                    op_code_list[i] = [x['id'] for x in self.game_data.gforce_data_json['gforce'] if x['name'] == op_code_list[i]][0]
                elif param_type == "target_slot":
                    op_code_list[i] = [x['id'] for x in self.__get_target_list(advanced=True, specific=True, slot=True) if x['data'] == op_code_list[i]][0]
                elif param_type == "target_advanced_specific":
                    op_code_list[i] = [x['id'] for x in self.__get_target_list(advanced=True, specific=True) if x['data'] == op_code_list[i]][0]
                elif param_type == "target_advanced_generic":
                    op_code_list[i] = [x['id'] for x in self.__get_target_list(advanced=True, specific=False) if x['data'] == op_code_list[i]][0]
                elif param_type == "target_basic":
                    op_code_list[i] = [x['id'] for x in self.__get_target_list(advanced=False, specific=False) if x['data'] == op_code_list[i]][0]
                elif param_type == "comparator":
                    op_code_list[i] = self.game_data.ai_data_json['list_comparator_ifritAI'].index(op_code_list[i])
                elif param_type == "status_ai":
                    op_code_list[i] = [x['id'] for x in self.game_data.status_data_json['status_ai'] if x['name'] == op_code_list[i]][0]
                elif param_type == "magic_type":
                    op_code_list[i] = [x['id'] for x in self.game_data.magic_data_json['magic_type'] if x['name'] == op_code_list[i]][0]
                elif param_type == "aptitude":
                    op_code_list[i] = [x['aptitude_id'] for x in self.game_data.ai_data_json['aptitude_list'] if x['text'] == op_code_list[i]][0]
                elif param_type == "battle_text":
                    if int(op_code_list[i]) < len(self.__battle_text):
                        op_code_list[i] = int(op_code_list[i])
                    else:
                        print(f"Battle text index {op_code_list[i]} not found in list : {self.__battle_text}")
                else:
                    print(f"Text data analysis - Unknown type {param_type}, considering a int")
                    op_code_list[i] = int(op_code_list[i])
        elif op_info['op_code'] == 2:  # IF
            # Subject ID (0)
            op_code_list[0] = int(op_code_list[0])
            subject_id = op_code_list[0]
            # Left condition (1)
            if_subject_dict = [x for x in self.game_data.ai_data_json['if_subject'] if x['subject_id'] == subject_id]
            if if_subject_dict:
                if_subject_dict = if_subject_dict[0]
            elif subject_id > 20:  # It's a var
                if_subject_dict = {"subject_id": subject_id, "short_text": "VAR Subject",  # For a var, subject ID need to be 200 for local var
                                   "left_text": '{}', "complexity": "simple", "param_left_type": "const",
                                   "param_right_type": "int", "param_list": [200]}
            ## Now we want to have only the parameter of the subject, for this we remove data around
            split_text = if_subject_dict['left_text'].split('{}')
            if_subject_left_parameter_text = op_code_list[1].replace(split_text[0], '')
            temp_int_right = 0  # To handle special cases of subj ID 15 where text and int are inversed
            if len(split_text) > 1:
                if_subject_left_parameter_text = if_subject_left_parameter_text.replace(split_text[1], '')
            if if_subject_dict['param_left_type'] == "int":
                op_code_list[1] = int(if_subject_left_parameter_text)
            elif if_subject_dict['param_left_type'] == "int_shift":
                shift = if_subject_dict['param_list'][0]
                op_code_list[1] = int(if_subject_left_parameter_text) - shift
            elif if_subject_dict['param_left_type'] == "int_right":
                temp_int_right = if_subject_left_parameter_text
                op_code_list[1] = 200  # Always ALIVE
            elif if_subject_dict['param_left_type'] == "var":
                op_code_list[1] = [x['op_code'] for x in self.game_data.ai_data_json['list_var'] if x['var_name'] == if_subject_left_parameter_text][0]
            elif if_subject_dict['param_left_type'] == "subject10":  # We don't use if_subject_left_parameter_text
                subject10_list = [x['param_id'] for x in self.game_data.ai_data_json['subject_left_10'] if op_code_list[1] in x['text']]
                if not subject10_list:
                    print(f"Unexpected subject10: {op_code_list[1]}")
                    op_code_list[1] = 0
                else:
                    op_code_list[1] = subject10_list[0]
            elif if_subject_dict['param_left_type'] == "int_shift":
                if if_subject_dict['subject_id'] == 2:
                    shift = 1
                else:
                    print("unexpected int_shift for subject id: {}")
                op_code_list[1] = int(if_subject_left_parameter_text) + shift
            elif if_subject_dict['param_left_type'] in ("target_advanced_specific", "target_advanced_generic"):
                if if_subject_dict['param_left_type'] == "target_advanced_specific":
                    target_list = self.__get_target_list(advanced=True, specific=True)
                if if_subject_dict['param_left_type'] == "target_advanced_generic":
                    target_list = self.__get_target_list(advanced=True, specific=False)
                target_id = [x['id'] for x in target_list if x['data'] == if_subject_left_parameter_text][0]
                op_code_list[1] = int(target_id)
            elif if_subject_dict['param_left_type'] == "const":
                op_code_list[1] = if_subject_dict['param_list'][0]  # Unused
            elif if_subject_dict['param_left_type'] == "":
                op_code_list[1] = 0  # Unused
            else:
                print(f"Unexpected if_subject_dict['param_left_type']: {if_subject_dict['param_left_type']}")
                op_code_list[1] = 0
            # Comparison (2)
            op_code_list[2] = self.game_data.ai_data_json['list_comparator_ifritAI'].index(op_code_list[2])
            # Right condition (3)
            r_cond = op_code_list[3]
            if if_subject_dict['param_right_type'] == "int":
                op_code_list[3] = int(r_cond)
            elif if_subject_dict['param_right_type'] == "alive":
                op_code_list[3] = int(temp_int_right) + 3
            elif if_subject_dict['param_right_type'] == "gender":
                op_code_list[3] = [x['id'] for x in self.game_data.ai_data_json['gender_type'] if x['type'] == r_cond][0]
            elif if_subject_dict['param_right_type'] == "percent":
                op_code_list[3] = int(int(r_cond.replace(' %', '')) / 10)
            elif if_subject_dict['param_right_type'] == "status_ai":
                op_code_list[3] = [x['id'] for x in self.game_data.status_data_json['status_ai'] if x['name'] == r_cond][0]
            elif if_subject_dict['param_right_type'] == "target_advanced_specific":
                target_list = self.__get_target_list(advanced=True, specific=True)
                op_code_list[3] = [x['id'] for x in target_list if x['data'] == r_cond][0]
            elif if_subject_dict['param_right_type'] == "target_advanced_generic":
                target_list = self.__get_target_list(advanced=True, specific=False)
                op_code_list[3] = [x['id'] for x in target_list if x['data'] == r_cond][0]
            elif if_subject_dict['param_right_type'] == "const":
                op_code_list[3] = if_subject_dict['param_list'][1]  # Unused
            elif if_subject_dict['param_right_type'] == "complex":
                if subject_id == 10:
                    if op_code_list[1] == 0:  # Attack type
                        search_value = [x['id'] for x in self.game_data.ai_data_json['attack_type'] if x['type'] == op_code_list[3]]
                        if search_value:
                            op_code_list[3] = search_value[0]
                        else:
                            print(f"Unexpected attack type: {op_code_list[3]}")
                            op_code_list[3] = 0
                    elif op_code_list[1] == 1:  # Target advanced specific
                        search_value = [x['id'] for x in self.__get_target_list(advanced=True, specific=True) if x['data'] == op_code_list[3]]
                        if search_value:
                            op_code_list[3] = search_value[0]
                        else:
                            print(f"Unexpected target advanced specific: {op_code_list[3]}")
                            op_code_list[3] = 0
                    elif op_code_list[1] == 2:  # TURN COUNTER INT
                        op_code_list[3] = int(op_code_list[3])
                    elif op_code_list[1] == 3:  # Command type
                        search_value = [x['id'] for x in self.game_data.ai_data_json['command_type'] if x['data'] == op_code_list[3]]
                        if search_value:
                            op_code_list[3] = search_value[0]
                        else:
                            print(f"Unexpected target advanced specific: {op_code_list[3]}")
                            op_code_list[3] = 0
                        if op_code_list[3] == 1:
                            self.was_physical = True
                        elif op_code_list[3] == 2:
                            self.was_magical = True
                        elif op_code_list[3] == 4:
                            self.was_item = True
                        elif op_code_list[3] == 254:
                            self.was_gforce = True
                    elif op_code_list[1] == 4:  # Last Command type or gforce
                        # First Gforce
                        search_value = [x['id'] for x in self.game_data.gforce_data_json['command_type'] if x['name'] == op_code_list[3]]
                        if search_value:
                            op_code_list[3] = search_value[0] + 64
                        else:
                            if self.was_physical:
                                search_value = [x['id'] for x in self.game_data.special_action_data_json['special_action'] if x['name'] == op_code_list[3]]
                                if search_value:
                                    op_code_list[3] = search_value[0]
                                else:
                                    print(f"Unexpected last command type physical: {op_code_list[3]}")
                                    op_code_list[3] = 0
                            elif self.was_magic:
                                search_value = [x['id'] for x in self.game_data.magic_data_json['magic'] if x['name'] == op_code_list[3]]
                                if search_value:
                                    op_code_list[3] = search_value[0]
                                else:
                                    print(f"Unexpected last command type magic: {op_code_list[3]}")
                                    op_code_list[3] = 0
                            elif self.was_item:
                                search_value = [x['id'] for x in self.game_data.item_data_json['items'] if x['name'] == op_code_list[3]]
                                if search_value:
                                    op_code_list[3] = search_value[0]
                                else:
                                    print(f"Unexpected last command type item: {op_code_list[3]}")
                                    op_code_list[3] = 0
                            else:
                                print(f"Unexpected last command type, not even gforce: {op_code_list[3]}")
                                op_code_list[3] = int(op_code_list[3])
                        self.was_gforce = False
                        self.was_item = False
                        self.was_magic = False
                        self.was_physical = False
                    elif op_code_list[1] == 5:  # Magic type
                        search_value = [x['id'] for x in self.game_data.magic_data_json['magic_type'] if x['name'] == op_code_list[3]]
                        if search_value:
                            op_code_list[3] = search_value[0]
                        else:
                            print(f"Unexpected magic type: {op_code_list[3]}")
                            op_code_list[3] = 0
                    else:
                        print(f"Unexpected param right for subject id 10: {op_code_list[3]}")
                        op_code_list[3] = 0
                else:
                    print(f"Unexpected if subject param right type: {if_subject_dict['param_right_type']}")
            # Unused value (called debug)
            op_code_list[4] = int(op_code_list[4])
            # Expanding jump
            op_code_list[5] = int(op_code_list[5])
            op_code_list[6] = int(op_code_list[6])
        elif op_info['op_code'] == 45:
            op_code_list[0] = [x['id'] for x in self.game_data.magic_data_json['magic_type'] if x['name'] == op_code_list[0]]
            if op_code_list[0]:
                op_code_list[0] = op_code_list[0][0]
            else:
                print("Unexpected magic type for elem id 45")
            op_code_list[1] = int(op_code_list[1])
            op_code_list[2] = int(op_code_list[2])

        self.set_op_code(op_code_list)

    def __analyse_op_data(self):
        self.reset_data()
        op_info = self.__get_op_code_line_info()
        # Searching for errors in json file
        if len(op_info["param_type"]) != op_info["size"] and op_info['complexity'] == 'simple':
            print(f"Error on JSON for op_code_id: {self.__op_id}")
        if op_info["complexity"] == "simple":
            param_value = []
            for index, type in enumerate(op_info["param_type"]):
                op_index = op_info["param_index"][index]
                self.type_data.append(type)
                if type == "int":
                    param_value.append(str(self.__op_code[op_index]))
                    self.param_possible_list.append([])
                elif type == "int_shift":
                    shift = op_info['param_list'][0]
                    param_value.append(str(self.__op_code[op_index] + shift))
                    self.param_possible_list.append([])
                elif type == "percent":
                    param_value.append(str(self.__op_code[op_index] * 10))
                    self.param_possible_list.append([])
                elif type == "magic_type":
                    param_value.append(str([x['name'] for x in self.game_data.magic_data_json['magic_type'] if x['id'] == self.__op_code[op_index]]))
                    self.param_possible_list.append(self.__get_possible_magic_type())
                elif type == "bool":
                    param_value.append(str(bool(self.__op_code[op_index])))
                    self.param_possible_list.append([{"id": 0, "data": "True"}, {"id": 1, "data": "False"}])
                elif type == "activate":
                    param_value.append([x['name'] for x in self.game_data.ai_data_json['activate_type'] if x['id'] == self.__op_code[op_index]][0])
                    self.param_possible_list.append(self.__get_possible_activate())
                elif type == "var":
                    # There is specific var known, if not in the list it means it's a generic one
                    param_value.append(self.__get_var_name(self.__op_code[op_index]))
                    self.param_possible_list.append(self.__get_possible_var())
                elif type == "special_action":
                    if self.__op_code[op_index] < len(self.game_data.special_action_data_json["special_action"]):
                        param_value.append(self.game_data.special_action_data_json["special_action"][self.__op_code[op_index]]['name'])
                        self.param_possible_list.append(self.__get_possible_special_action())
                    else:
                        param_value.append("UNKNOWN SPECIAL_ACTION")
                elif type == "monster_line_ability":
                    possible_ability_values = []
                    nb_ability_high = len([x for x in self.info_stat_data['abilities_high'] if x['id'] != 0])
                    nb_ability_med = len([x for x in self.info_stat_data['abilities_med'] if x['id'] != 0])
                    nb_ability_low = len([x for x in self.info_stat_data['abilities_low'] if x['id'] != 0])
                    nb_abilities = max(nb_ability_high, nb_ability_med, nb_ability_low)
                    for i in range(nb_abilities):
                        if self.info_stat_data['abilities_high'][i] != 0:
                            if self.info_stat_data['abilities_high'][i]['type'] == 2:  # Magic
                                high_text = self.game_data.magic_data_json["magic"][self.info_stat_data['abilities_high'][i]['id']]['name']
                            elif self.info_stat_data['abilities_high'][i]['type'] == 4:  # Item
                                high_text = self.game_data.item_data_json["items"][self.info_stat_data['abilities_high'][i]['id']]['name']
                            elif self.info_stat_data['abilities_high'][i]['type'] == 8:  # Ability
                                high_text = self.game_data.enemy_abilities_data_json["abilities"][self.info_stat_data['abilities_high'][i]['id']]['name']
                            elif self.info_stat_data['abilities_high'][i]['type'] == 0:  # Emptyness
                                high_text = "None"
                            else:
                                high_text = "Unexpected type ability"
                        else:
                            high_text = "None"
                        if self.info_stat_data['abilities_med'][i] != 0:
                            if self.info_stat_data['abilities_med'][i]['type'] == 2:  # Magic
                                med_text = self.game_data.magic_data_json["magic"][self.info_stat_data['abilities_med'][i]['id']]['name']
                            elif self.info_stat_data['abilities_med'][i]['type'] == 4:  # Item
                                med_text = self.game_data.item_data_json["items"][self.info_stat_data['abilities_med'][i]['id']]['name']
                            elif self.info_stat_data['abilities_med'][i]['type'] == 8:  # Ability
                                med_text = self.game_data.enemy_abilities_data_json["abilities"][self.info_stat_data['abilities_med'][i]['id']]['name']
                            elif self.info_stat_data['abilities_med'][i]['type'] == 0:  # Emptyness
                                med_text = "None"
                            else:
                                med_text = "Unexpected type ability"
                        else:
                            med_text = "None"
                        if self.info_stat_data['abilities_low'][i] != 0:
                            if self.info_stat_data['abilities_low'][i]['type'] == 2:  # Magic
                                low_text = self.game_data.magic_data_json["magic"][self.info_stat_data['abilities_low'][i]['id']]['name']
                            elif self.info_stat_data['abilities_low'][i]['type'] == 4:  # Item
                                low_text = self.game_data.item_data_json["items"][self.info_stat_data['abilities_low'][i]['id']]['name']
                            elif self.info_stat_data['abilities_low'][i]['type'] == 8:  # Ability
                                low_text = self.game_data.enemy_abilities_data_json["abilities"][self.info_stat_data['abilities_low'][i]['id']]['name']
                            elif self.info_stat_data['abilities_low'][i]['type'] == 0:  # Emptyness
                                low_text = "None"
                            else:
                                low_text = "Unexpected type ability"
                        else:
                            low_text = "None"
                        text = f"Low - {low_text} | Med - {med_text} | High - {high_text}"
                        possible_ability_values.append({'id': i, 'data': text})
                        if self.__op_code[op_index] == i:
                            param_value.append(f"{i}")
                            self.__raw_text_added.append({"id": len(param_value) - 1, "text": " (" + text + " )", "text_html": " (" + text + " )<br/>"})
                    if self.__op_code[op_index] >= nb_abilities:
                        param_value.append(253)
                        self.__raw_text_added.append({"id": 253, "text": " (None) ", "text_html": " (None) "})
                    else:
                        possible_ability_values.append({'id': 0, 'data': "None"})  # 253 for None value is often used by monsters.
                    self.param_possible_list.append(possible_ability_values)

                elif type == "battle_text":
                    if self.__op_code[op_index] < len(self.__battle_text):
                        battle_text_str = self.__battle_text[self.__op_code[op_index]].get_str()
                        param_value.append(self.__op_code[op_index])
                        self.param_possible_list.append(self.__get_possible_battle_text())
                        self.__raw_text_added.append({"id": len(param_value) - 1, "text": " (" + battle_text_str + " )", "text_html": " (" + battle_text_str + " )"})
                    else:
                        param_value.append("UNKNOWN BATTLE TEXT")
                elif type == "ability":
                    if self.__op_code[op_index] < len(self.game_data.enemy_abilities_data_json["abilities"]):
                        param_value.append(self.game_data.enemy_abilities_data_json["abilities"][self.__op_code[op_index]]['name'])
                        self.param_possible_list.append(self.__get_possible_ability())
                    else:
                        param_value.append("UNKNOWN CARD")
                elif type == "card":
                    if self.__op_code[op_index] < len(self.game_data.card_data_json["card_info"]):
                        param_value.append(self.game_data.card_data_json["card_info"][self.__op_code[op_index]]['name'])
                        self.param_possible_list.append(self.__get_possible_card())
                    else:
                        param_value.append("UNKNOWN CARD")
                elif type == "monster":
                    if self.__op_code[op_index] < len(self.game_data.monster_data_json["monster"]):
                        param_value.append(self.game_data.monster_data_json["monster"][self.__op_code[op_index]]['name'])
                        self.param_possible_list.append(self.__get_possible_monster())
                    else:
                        param_value.append("UNKNOWN MONSTER")
                elif type == "item":
                    if self.__op_code[op_index] < len(self.game_data.item_data_json["items"]):
                        param_value.append(self.game_data.item_data_json["items"][self.__op_code[op_index]]['name'])
                        self.param_possible_list.append(self.__get_possible_item())
                    else:
                        param_value.append("UNKNOWN ITEM")
                elif type == "status_ai":
                    if self.__op_code[op_index] <= self.game_data.status_data_json["status_ai"][-1]['id']:
                        param_value_temp = [x['name'] for x in self.game_data.status_data_json["status_ai"] if x['id'] == self.__op_code[op_index]]
                        if param_value_temp:
                            param_value.append(param_value_temp[0])
                        else:
                            print(f"Unknown status for id: {self.__op_code[op_index]}")
                            param_value.append(self.__op_code[op_index])
                        self.param_possible_list.append(self.__get_possible_status_ai())
                    else:
                        param_value.append("UNKNOWN STATUS AI")
                elif type == "gforce":
                    if self.__op_code[op_index] < len(self.game_data.gforce_data_json["gforce"]):
                        param_value.append(self.game_data.gforce_data_json["gforce"][self.__op_code[op_index]]['name'])
                        self.param_possible_list.append(self.__get_possible_gforce())
                    else:
                        param_value.append("UNKNOWN GFORCE")
                elif type == "target_advanced_specific":
                    param_value.append(self.__get_target(self.__op_code[op_index], advanced=True, specific=True))
                    self.param_possible_list.append([x for x in self.__get_target_list(advanced=True, specific=True)])
                elif type == "target_advanced_generic":
                    param_value.append(self.__get_target(self.__op_code[op_index], advanced=True, specific=False))
                    self.param_possible_list.append([x for x in self.__get_target_list(advanced=True, specific=False)])
                elif type == "target_basic":
                    param_value.append(self.__get_target(self.__op_code[op_index], advanced=False))
                    self.param_possible_list.append([x for x in self.__get_target_list(advanced=False)])
                elif type == "target_slot":
                    param_value.append(self.__get_target(self.__op_code[op_index], advanced=False, slot=True))
                    self.param_possible_list.append([x for x in self.__get_target_list(advanced=False, slot=True)])
                elif type == "comparator":
                    param_value.append(self.game_data.ai_data_json['list_comparator'][self.__op_code[op_index]])
                    self.param_possible_list.append([{"id": i, "data": x} for i, x in enumerate(self.game_data.ai_data_json['list_comparator'])])
                elif type == "aptitude":
                    param_value.append([x['text'] for x in self.game_data.ai_data_json['aptitude_list'] if x['aptitude_id'] == self.__op_code[op_index]][0])
                    self.param_possible_list.append([{"id": x["aptitude_id"], "data": x['text']} for x in self.game_data.ai_data_json['aptitude_list']])
                else:
                    param_value.append(self.__op_code[op_index])
            # Now putting the op_list in the correct order for param value (data analysis already in correct order):
            original_param_possible = self.param_possible_list.copy()
            for i, param_index in enumerate(op_info['param_index']):
                self.param_possible_list[param_index] = original_param_possible[i]

            self.__raw_text = op_info['text']
            self.__raw_parameters = param_value

        elif op_info["complexity"] == "complex":
            call_function = getattr(self, "_CommandAnalyser__op_" + "{:02}".format(op_info["op_code"]) + "_analysis")
            call_result = call_function(self.__op_code)
            self.__raw_text = call_result[0]
            self.__raw_parameters = [str(x) for x in call_result[1]]
        self.__size = op_info['size'] + 1

    def __get_possible_target_advanced_specific(self):
        return [x for x in self.__get_target_list(advanced=True, specific=True)]

    def __get_possible_target_advanced_generic(self):
        return [x for x in self.__get_target_list(advanced=True, specific=False)]

    def __get_possible_var(self):
        return [{"id": x['op_code'], "data": x['var_name']} for x in self.game_data.ai_data_json["list_var"]]

    def __get_possible_magic(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.magic_data_json["magic"])]

    def __get_possible_magic_type(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.magic_data_json["magic_type"])]

    def __get_possible_item(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.item_data_json["items"])]

    def __get_possible_status_ai(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.status_data_json["status_ai"])]

    def __get_possible_gforce(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.gforce_data_json["gforce"])]

    def __get_possible_monster(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.monster_data_json["monster"])]

    def __get_possible_card(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.card_data_json["card_info"])]

    def __get_possible_status_ai(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.status_data_json["status_ai"])]

    def __get_possible_gender(self):
        return [{'id': val_dict['id'], 'data': val_dict['type']} for id, val_dict in enumerate(self.game_data.ai_data_json["gender_type"])]

    def __get_possible_special_action(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.special_action_data_json["special_action"])]

    def __get_possible_ability(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.enemy_abilities_data_json["abilities"])]

    def __get_possible_battle_text(self):
        return [{'id': i, 'data': data.get_str()} for i, data in enumerate(self.__battle_text)]

    def __get_possible_activate(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.ai_data_json["activate_type"])]

    def __op_35_analysis(self, op_code):
        op_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x['op_code'] == 35][0]
        jump = int.from_bytes(bytearray([op_code[0], op_code[1]]), byteorder='little')
        self.param_possible_list.append([])
        self.param_possible_list.append([])
        if jump == 0:
            return [op_info['text'][0], []]
        else:
            return [op_info['text'][1], [jump]]

    def __op_45_analysis(self, op_code):
        if op_code[0] < len(self.game_data.magic_data_json['magic_type']):
            element = self.game_data.magic_data_json['magic_type'][op_code[0]]['name']
        else:
            element = "UNKNOWN ELEMENT TYPE"
        target = op_code[1] + 256 * op_code[2]
        element_val = 900 - target
        self.param_possible_list.append(self.__get_possible_magic_type())
        self.param_possible_list.append([])
        op_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x['op_code'] == 45][0]
        return [op_info['text'], [element, element_val]]

    def __op_02_analysis(self, op_code):
        # op_02 = ['subject_id', 'left condition (target)', 'comparator', 'right condition (value)', 'jump1', 'jump2', 'debug']
        op_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x['op_code'] == 2][0]
        subject_id = op_code[0]
        op_code_left_condition_param = op_code[1]
        op_code_comparator = op_code[2]
        op_code_right_condition_param = op_code[3]
        debug_unknown = op_code[4]
        jump_value_op_1 = op_code[5]
        jump_value_op_2 = op_code[6]
        jump_value = int.from_bytes(bytearray([op_code[5], op_code[6]]), byteorder='little')
        if op_code_comparator < len(self.game_data.ai_data_json['list_comparator']):
            comparator = self.game_data.ai_data_json['list_comparator'][op_code_comparator]
        else:
            comparator = 'UNKNOWN OPERATOR'

        if_text = op_info["text"]
        if_current_subject = [x for x in self.game_data.ai_data_json["if_subject"] if x["subject_id"] == subject_id]
        list_param_possible_left = []
        list_param_possible_right = []

        if if_current_subject:
            if_current_subject = if_current_subject[0]
        elif subject_id > 20:
            left_subject = {'text': '{}', 'param': self.__get_var_name(subject_id)}
            right_subject = {'text': '{}', 'param': [int(op_code_right_condition_param)]}
        else:
            left_subject = {'text': 'UNKNOWN SUBJECT', 'param': None}
            right_subject = {'text': '{}', 'param': [op_code_right_condition_param]}
            print(f"Unexpected subject id: {subject_id}")

        # Analysing left subject
        if if_current_subject:
            specific_left_text = ""
            if if_current_subject["complexity"] == "simple":
                if if_current_subject['param_left_type'] == "target_basic":
                    param_left = self.__get_target(op_code_left_condition_param, advanced=False)
                    list_param_possible_left.extend(self.__get_target_list(advanced=False))
                elif if_current_subject['param_left_type'] == "target_slot":
                    param_left = self.__get_target(op_code_left_condition_param, advanced=False, slot=True)
                    list_param_possible_left.extend(self.__get_target_list(advanced=False, slot=True))
                elif if_current_subject['param_left_type'] == "target_advanced_generic":
                    param_left = self.__get_target(op_code_left_condition_param, advanced=True, specific=False)
                    list_param_possible_left.extend(self.__get_target_list(advanced=True, specific=False))
                elif if_current_subject['param_left_type'] == "target_advanced_specific":
                    param_left = self.__get_target(op_code_left_condition_param, advanced=True, specific=True)
                    list_param_possible_left.extend(self.__get_target_list(advanced=True, specific=True))
                elif if_current_subject['param_left_type'] == "int":
                    param_left = int(op_code_left_condition_param)
                elif if_current_subject['param_left_type'] == "int_shift":
                    shift = if_current_subject['param_list'][0]
                    param_left = int(op_code_left_condition_param) + shift
                elif if_current_subject['param_left_type'] == "int_right":
                    shift = if_current_subject['param_list'][0]
                    param_left = int(op_code_right_condition_param) + shift
                elif if_current_subject['param_left_type'] == "const":
                    param_left = if_current_subject['left_text']
                    list_param_possible_left.extend([{"id":if_current_subject['param_list'][0], "data": if_current_subject['left_text']}])
                elif if_current_subject['param_left_type'] == "subject10":
                    param_left = []
                    if op_code_left_condition_param >= 200:  # Basic target
                        specific_left_text = [x['text'] for x in self.game_data.ai_data_json['target_basic'] if x['param_id'] == op_code_left_condition_param]
                        if specific_left_text:
                            specific_left_text = specific_left_text[0]
                        else:
                            print(f"Didn't find a target in subject 10 for code {op_code_left_condition_param}")
                            specific_left_text = 0
                    else:
                        subject_left_data = [x['text'] for x in self.game_data.ai_data_json['subject_left_10'] if x['param_id'] == op_code_left_condition_param]
                        if not subject_left_data:
                            if_current_subject["left_text"] = "Unknown last attack {}".format(op_code_left_condition_param)
                        else:
                            if op_code_left_condition_param == 2:
                                specific_left_text = subject_left_data[0][0]
                            elif op_code_left_condition_param == 4:
                                if op_code_right_condition_param < 64:
                                    specific_left_text = subject_left_data[0][1]
                                else:
                                    specific_left_text = subject_left_data[0][0]
                            else:
                                specific_left_text = subject_left_data[0][0]
                    sum_text = ""
                    list_param_possible_left.extend(
                        [{'id': x['param_id'], 'data': [sum_text + y for y in x['text']][-1]} for x in self.game_data.ai_data_json['subject_left_10']])
                elif if_current_subject['param_left_type'] == "":
                    param_left = "UNKNOWN {}".format(op_code_left_condition_param)
                else:
                    print("Unexpected param_left_type: {}".format(if_current_subject['param_left_type']))
                    param_left = op_code_left_condition_param
                    list_param_possible_left.append({"id": op_code_left_condition_param, "data": "Unused"})
            elif if_current_subject["complexity"] == "complex":
                if if_current_subject["subject_id"] == 15:  # ALLY SLOT X IS ALIVE
                    param_left = op_code_right_condition_param - 3  # Special case where we take the right condition
                else:
                    print(f"Unexpected subject_id: {if_current_subject["subject_id"]}")
                    param_left = op_code_left_condition_param
            else:
                print(f"Unexpected complexity: {if_current_subject["complexity"]}")
                param_left = op_code_left_condition_param
            if not specific_left_text:
                specific_left_text = if_current_subject["left_text"]
            left_subject = {'text': specific_left_text, 'param': param_left}

        # Analysing right subject
        if if_current_subject:
            right_param_type = if_current_subject['param_right_type']
            if right_param_type:
                if right_param_type == 'percent':
                    right_subject = {'text': '{} %', 'param': [op_code_right_condition_param * 10]}
                elif right_param_type == 'alive':
                    right_subject = {'text': 'ALIVE', 'param': []}
                elif right_param_type == "const":
                    right_subject = {'text': if_current_subject['right_text'], 'param': []}
                    list_param_possible_right = [{"id":if_current_subject['param_list'][1], "data": if_current_subject['right_text']}]
                elif right_param_type == 'gender':
                    param = [x['type'] for x in self.game_data.ai_data_json["gender_type"] if x['id'] == op_code_right_condition_param]
                    if not param:
                        print(f"Gender {op_code_right_condition_param} not found")
                    right_subject = {'text': '{}', 'param': [param[0]]}
                    list_param_possible_right = self.__get_possible_gender()
                elif right_param_type == 'int':
                    right_subject = {'text': '{}', 'param': [op_code_right_condition_param]}
                elif right_param_type == 'status_ai':
                    param = [x['name'] for x in self.game_data.status_data_json["status_ai"] if x['id'] == op_code_right_condition_param]
                    if not param:
                        print(f"status_ai {op_code_right_condition_param} not found")
                    right_subject = {'text': '{}', 'param': [param[0]]}
                    list_param_possible_right = self.__get_possible_status_ai()
                elif right_param_type == 'target_advanced_specific':
                    right_subject = {'text': '{}', 'param': [self.__get_target(op_code[3], advanced=True, specific=True)]}
                elif right_param_type == 'text':
                    right_subject = {'text': '{}', 'param': [x['right_text'] for x in self.game_data.ai_data_json['if_subject'] if x['subject_id'] == subject_id]}
                elif right_param_type == 'target_advanced_generic':
                    right_subject = {'text': '{}', 'param': [self.__get_target(op_code[3], advanced=True, specific=False)]}
                    list_param_possible_right = self.__get_possible_target_advanced_specific()
                elif right_param_type == 'complex' and subject_id == 10:
                    attack_right_text = "{}"
                    attack_right_condition_param = [str(op_code[3])]
                    if op_code[1] == 0:
                        list_param_possible_right.extend([{"id": x['id'], "data": x['type']} for x in self.game_data.ai_data_json['attack_type']])
                        attack_right_condition_param = [self.game_data.ai_data_json['attack_type'][op_code_right_condition_param]['type']]
                    elif op_code[1] == 1:
                        attack_right_condition_param = [self.__get_target(op_code_right_condition_param, advanced=True, specific=True)]
                        list_param_possible_right.extend(self.__get_possible_target_advanced_specific())
                    elif op_code[1] == 2:  # Turn counter
                        attack_right_condition_param = [int(op_code_right_condition_param)]
                    elif op_code[1] == 3:  # Need to handle better the was_magic
                        list_param_possible_right.extend([{"id": x['id'], "data": x['data']} for x in self.game_data.ai_data_json['command_type']])
                        attack_right_condition_param = [x['data'] for x in self.game_data.ai_data_json['command_type'] if x['id'] == op_code_right_condition_param]
                        if not attack_right_condition_param:
                            attack_right_condition_param = ["Unknown {}".format(op_code_right_condition_param)]
                        if op_code_right_condition_param == 1:
                            self.was_physical = True
                        elif op_code_right_condition_param == 2 or op_code_right_condition_param == 6:
                            self.was_magic = True
                        elif op_code_right_condition_param == 4:
                            self.was_item = True
                        elif op_code_right_condition_param == 254:
                            self.was_gforce = True
                        else:
                            print(f"Unknown condition type for subject 10 op code 3: {op_code_right_condition_param}")
                    elif op_code[1] == 4:
                        if op_code_right_condition_param >= 64:
                            attack_right_condition_param = [self.game_data.gforce_data_json["gforce"][op_code_right_condition_param - 64]['name']]
                            list_param_possible_right.extend(self.__get_possible_gforce())
                        else:
                            if self.previous_command.was_magic:
                                ret = self.game_data.magic_data_json["magic"][op_code_right_condition_param]['name']
                                list_param_possible_right.extend(self.__get_possible_magic())
                            elif self.previous_command.was_item:
                                ret = self.game_data.item_data_json["items"][op_code_right_condition_param]['name']
                                list_param_possible_right.extend(self.__get_possible_item())
                            elif self.previous_command.was_physical:
                                ret = self.game_data.special_action_data_json["special_action"][op_code_right_condition_param]['name']
                                list_param_possible_right.extend(self.__get_possible_special_action())
                            else:
                                ret = str(op_code_right_condition_param)
                            attack_right_condition_param = [ret]
                            self.previous_command.was_magic = False
                            self.previous_command.was_item = False
                            self.previous_command.was_physical = False
                            self.previous_command.was_gforce = False
                    elif op_code[1] == 5:
                        attack_right_condition_param = [str(self.game_data.magic_data_json['magic_type'][op_code_right_condition_param]['name'])]
                        list_param_possible_right.extend(self.__get_possible_magic_type())
                    elif op_code[1] >= 200:
                        attack_right_condition_param = [x['text'] for x in self.game_data.ai_data_json['target_advanced_generic'] if
                                                        x['param_id'] == op_code_right_condition_param]
                        if attack_right_condition_param:
                            attack_right_condition_param = attack_right_condition_param
                        else:
                            print(f"Target right condition not found for subject id 10 with code: {op_code_right_condition_param}")
                            attack_right_condition_param = [0]
                    else:
                        attack_right_condition_param = [op_code_right_condition_param]
                    right_subject = {'text': attack_right_text, 'param': attack_right_condition_param}
            else:
                print(f"Unexpected right_param_type: {right_param_type}")
                right_subject = {'text': '{}', 'param': [op_code_right_condition_param]}
        if_text = if_text.format('{}', left_subject['text'], '{}', '{}', '{}', '{}')
        right_subject_text = right_subject['text'].format(*right_subject['param'])

        param_possible_sub_id = []
        param_possible_sub_id.extend(
            [{"id": x['subject_id'], "data": x['short_text']} for x in self.game_data.ai_data_json["if_subject"]])
        param_possible_sub_id.extend(
            [{"id": x['op_code'], "data": x['var_name']} for x in self.game_data.ai_data_json["list_var"]])
        # op_02 = ['subject_id', 'left condition (target)', 'comparator', 'right condition (value)', 'jump1', 'jump2', 'debug']
        # List of "Subject id" possible list
        self.param_possible_list.append(param_possible_sub_id)
        # List of "Left subject" possible list
        if if_current_subject:
            self.param_possible_list.append(list_param_possible_left)
        else:
            self.param_possible_list.append([{"id": op_code_left_condition_param, "data": "UNUSED"}])
        # List of "Comparator" possible list
        self.param_possible_list.append([{"id": i, "data": self.game_data.ai_data_json["list_comparator"][i]} for i in
                                         range(len(self.game_data.ai_data_json["list_comparator"]))])
        # List of "Right subject" possible list
        self.param_possible_list.append(list_param_possible_right)
        # List of "Jump1" possible list
        self.param_possible_list.append([])
        # List of "Jump2" possible list
        self.param_possible_list.append([])
        # List of "Debug" possible list
        self.param_possible_list.append([])

        list_param = [subject_id, left_subject['param'], comparator, right_subject_text, jump_value]
        if '{}' not in left_subject['text']:
            del list_param[1]
        return [if_text,list_param]

    def __get_var_name(self, id):
        # There is specific var known, if not in the list it means it's a generic one
        all_var_info = self.game_data.ai_data_json["list_var"]
        var_info_specific = [x for x in all_var_info if x["op_code"] == id]
        if var_info_specific:
            var_info_specific = var_info_specific[0]['var_name']
        else:
            var_info_specific = "var" + str(id)
        return var_info_specific

    def __get_target_list(self, advanced=False, specific=False, slot=False):
        list_target = []
        # The target list has 4 different type of target:
        # 1. The characters
        # 2. All monsters of the game
        # 3. Special target
        # 4. Target stored in variable

        if not slot:
            for i in range(len(self.game_data.ai_data_json['list_target_char'])):
                list_target.append({"id": i, "data": self.game_data.ai_data_json['list_target_char'][i]})
            for i in range(0, len(self.game_data.monster_data_json["monster"])):
                list_target.append({"id": i + 16, "data": self.game_data.monster_data_json["monster"][i]["name"]})
            number_of_generic_var_read = 0
            for var_data in self.game_data.ai_data_json['list_var']:
                if var_data['op_code'] == 220 + number_of_generic_var_read:
                    list_target.append({"id": number_of_generic_var_read + 220, "data": "TARGET CONTAINED IN VAR " + var_data['var_name']})
                    number_of_generic_var_read += 1
        if slot:
            list_target_data = self.game_data.ai_data_json['target_slot']
        elif advanced:
            if specific:
                list_target_data = self.game_data.ai_data_json['target_advanced_specific']
            else:
                list_target_data = self.game_data.ai_data_json['target_advanced_generic']
        else:
            list_target_data = self.game_data.ai_data_json['target_basic']

        for el in list_target_data:
            if el['param_type'] == "monster_name":
                data = "self"
            elif el['param_type'] == "":
                data = None
            else:
                print("Unexpected param type for target: {}".format(el['param_type']))
                data = None
            if data:
                text = el['text'].format(data)
            else:
                text = el['text']
            list_target.append({"id": el['param_id'], "data": text})
        return list_target

    def __get_target(self, id, advanced=False, specific=False, slot=False):
        target = [x['data'] for x in self.__get_target_list(advanced, specific, slot) if x['id'] == id]
        if target:
            return target[0]
        else:
            print("Unexpected target with id: {}".format(id))
            return "UNKNOWN TARGET"




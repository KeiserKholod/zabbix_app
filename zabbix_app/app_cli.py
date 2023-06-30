import argparse
import sys
import time
from datetime import datetime
import os 


class TimeMeasurement():
    """Класс для хранения и вывода на экран информации по времени работы программы"""

    def __init__(self, total_time):
        self.total_time = total_time.__str__()
        parsed = self.total_time.split(":") #hour,min,sec.ms
        self.hours = int(parsed[0])
        self.minutes = int(parsed[1])
        self.seconds = int(float(parsed[2]))

    def __str__(self):
        return "TOTAL TIME: " + str(self.hours) + \
            " hours; " + str(self.minutes) + \
            " minutes; " + str(self.seconds) + \
            " seconds"

    def __repr__(self):
        return self.__str__()


class InitArgsParser():
    """Класс для сбора и хранения аргументов и конфгураций из коммандной строки и файла zabapp.conf"""

    def __init__(self, dir_path):
        self.dir_path = dir_path
        self.parser = self.create_cli_parser()
        self.cli_args_obj = self.parser.parse_args()
        self.cli_args_dict = self.__get_cli_dict(vars(self.cli_args_obj))
        self.config_args_dict = self.parse_config_args(self.get_config_args())

    def create_cli_parser(self):
        """Создает обьект argparse и записывает в него аргументы командной строки"""
        parser = argparse.ArgumentParser()
        parser.add_argument('-l', '--log', default=None, dest="log",
                            help='Записывать лог в файл <filename>')
        parser.add_argument('--link', default=None,
                            help='Адрес Zabbix сервера.\nПример: Http://zabbix.local/zabbix')
        parser.add_argument('-n', '--login', default=None, dest="login",
                            help='Имя пользователя Zabbix')
        parser.add_argument('-p', '--pass', default=None, dest="pass",
                            help='Имя пользователя Zabbix')
        parser.add_argument('-g', '--git', default=None, dest="git",
                            help='Адрес GIT-сервера')
        parser.add_argument('-c', '--conf', default=None, dest="conf_file",
                            help='Изменить адрес конфигурационного файла zabapp.conf <filepath>')
        parser.add_argument('-u', '--cpu', default=None, dest="max_cpu",
                            help='Максимальное количество логических процессоров, занимаемое программой')
        parser.add_argument('-s', '--set', action='store_true', dest="set_conf",
                            help='Изменить конфигурации хостов из файла to_change.conf')
        return parser

    def get_config_args(self):
        """Получает данные из конфигурационного файла без комментариев"""
        conf_file = os.path.join(self.dir_path, "zabapp.conf")
        keys = self.cli_args_dict.keys()
        if keys.__contains__("conf_file"):
            conf_file = self.cli_args_dict["conf_file"]
        data = []
        with open(conf_file, "r") as file:
            for line in file.readlines():
                if line.find("#") == -1:
                    data.append(line.replace(" ", ""))
        return "\n".join(data)

    def get_to_change_hosts(self):
        """Получает данные из файла с хостами для изменений без комментариев"""
        to_change_file = "to_change.conf"
        keys = self.cli_args_dict.keys()
        if keys.__contains__("to_change"):
            to_change_file = self.cli_args_dict["to_change"]
        data = []
        with open(to_change_file, "r") as file:
            for line in file.readlines():
                if line.find("#") == -1:
                    data.append(line)
        return data

    def parse_config_args(self, raw_args: str):
        """Сохраняет данные, полученные из конфигурационного файла в словарь"""
        conf_dict = dict()
        lines = raw_args.split("\n")
        for line in lines:
            if line != "":
                key, value = line.split("=")
                key = key.replace(" ", "")
                value.replace(" ", "")
                conf_dict[key] = value

        return conf_dict

    def __get_cli_dict(self, args: dict):
        """Возвращает словарь аргументов командной строки без пустых полей"""
        clean_args = dict()
        for key in args.keys():
            value = args[key]
            if value is not None:
                clean_args[key] = value
        return clean_args

    def get_all_args(self):
        """Возвращает обьединение аргументов из cli и .conf с преимуществом у  cli"""
        result = dict(self.config_args_dict)
        for key in self.cli_args_dict.keys():
            result[key] = self.cli_args_dict[key]

        return result


def write_log_file(log_path, txt):
    """Запись лога в файл и консоль"""
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(txt + "; " + time + "; " + "\n")
    if not (log_path is None):
        with open(log_path, "a+") as file:
            file.write(txt + "; " + time + "; " + "\n")

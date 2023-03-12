import argparse
import sys


def create_cl_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log', default=None, dest="do_log",
                        help='Записывать лог в файл <filename>')
    parser.add_argument('link', default=None,
                        help='Адрес Zabbix сервера.\nПример: Http://zabbix.local/zabbix')
    parser.add_argument('-a', '--auth', default="admin root",
                        help='Имя пользователя Zabbix и пароль.\nПример: <login password>')
    parser.add_argument('-g', '--git', default=None,
                        help='Адрес GIT- сервера')
    parser.add_argument('-с', '--conf', default=None,
                        help='Считывать конфигурацию приложения из файла <filename>')
    return parser

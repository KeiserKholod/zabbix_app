import multiprocessing
import os
import subprocess
import sys

import zabbix_app.app_cli as app_cli
from zabbix_app.config_setter import ZabbixConfigSetter
from zabbix_app.zabbix_base import ZabbixObject
from zabbix_app.config_getter import ZabbixConfigGetter


def _get_conf_process(i, part, all_args):
    conf_getter = ZabbixConfigGetter(part, all_args)
    conf_getter.get_all_objects_configs()
    conf_getter.write_configs_on_disk()
    print("Get Successful; Process: " + str(i))


def _set_conf_process(i, part, all_args):
    cs = ZabbixConfigSetter(part, all_args)
    cs.upd_config_for_all()
    print("Set Successful; Process: " + str(i))


def call_git(path_to_dir):
    current_dir = os.getcwd()

    os.chdir(path_to_dir)
    answ = subprocess.run(["git", "status"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).__str__()
    if answ.find("not a git repository") > -1:
        print("GIT: Creating git-repo")  # Hello from the other side
        answ = subprocess.run(["git", "init"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).__str__()
        if answ.find("initialized") > -1:
            print("GIT: Repo initialized in " + path_to_dir)

    answ = subprocess.run(["git", "status"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).__str__()
    if answ.find("untracked files present") > -1 or answ.find("Changes not staged for commit") > -1:
        answ = subprocess.run(["git", "add", "*"], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT).__str__()
        answ = subprocess.run(["git", "commit", "-m", '"message"'], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT).__str__()
        print("GIT: Commit created")
    else:
        print("GIT: nothing to commit")

    os.chdir(current_dir)


if __name__ == '__main__':
    init_args_parser = app_cli.InitArgsParser()
    all_args = init_args_parser.get_all_args()
    print(all_args)

    # узнаем доступное кол-во процессов для многопоточной работы
    cpu_striction = sys.maxsize
    if all_args.keys().__contains__("max_cpu"):
        cpu_striction = int(all_args["max_cpu"])
    threads_count = min(multiprocessing.cpu_count(), cpu_striction)

    zabbix_connection = ZabbixObject(all_args)
    print("Zabbix version: " + zabbix_connection.z_version["result"])

    # запись конфигов с диска на сервер
    if all_args["set_conf"]:
        hosts = init_args_parser.get_to_change_hosts()
        parts = zabbix_connection.get_part_hosts(hosts, threads_count)
        for part in parts:
            i = 0
            for part in parts:
                p = multiprocessing.Process(target=_set_conf_process, args=[i, part, all_args])
                p.start()
                i += 1

    # Получение конфигов с сервера
    else:
        all_hosts = zabbix_connection.get_host_list()
        parts = zabbix_connection.get_part_hosts(all_hosts, threads_count)
        i = 0
        process = []
        for part in parts:
            p = multiprocessing.Process(target=_get_conf_process, args=[i, part, all_args])
            p.start()
            process.append(p)
            i += 1
        # синхронизация с main процессом
        for p in process:
            p.join()
        call_git(all_args["saving_dir"])

import multiprocessing
import os
import subprocess
import sys
from datetime import datetime

import zabbix_app.app_cli as app_cli
from zabbix_app.config_setter import ZabbixConfigSetter
from zabbix_app.git_interractor import GitInterractor
from zabbix_app.zabbix_base import ZabbixObject
from zabbix_app.config_getter import ZabbixConfigGetter


def _get_conf_process(i, part, all_args, return_dict):
    conf_getter = ZabbixConfigGetter(part, all_args)
    conf_getter.get_all_objects_configs()
    # conf_getter.write_configs_on_disk()
    return_dict[i] = conf_getter.served
    print("Get Successful; Process: " + str(i))


def _set_conf_process(i, part, all_args, return_dict):
    cs = ZabbixConfigSetter(part, all_args)
    cs.upd_config_for_all()
    return_dict[i] = conf_getter.served
    print("Set Successful; Process: " + str(i))

def _get_served_hosts_count(return_dict):
    count = 0
    for key in return_dict.keys():
        count += return_dict[key]
    return count

if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    init_args_parser = app_cli.InitArgsParser(dir_path)
    all_args = init_args_parser.get_all_args()
    all_hosts_count = 0
    
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    threads_count = 0
    try:
        start_time = datetime.now()
        # print(all_args)

        # узнаем доступное кол-во процессов для многопоточной работы
        cpu_striction = sys.maxsize
        if all_args.keys().__contains__("max_cpu"):
            cpu_striction = int(all_args["max_cpu"])
        threads_count = min(multiprocessing.cpu_count(), cpu_striction)

        zabbix_connection = ZabbixObject(all_args)
        print("Zabbix version: " + zabbix_connection.z_version["result"])
        app_cli.write_log_file(all_args["log"], "#" * 5 + " SESSION START " + "#" * 5)

        # запись конфигов с диска на сервер
        if all_args["set_conf"]:
            hosts = init_args_parser.get_to_change_hosts()
            all_hosts_count = len(hosts)
            parts = zabbix_connection.get_part_hosts(hosts, threads_count)
            process = []
            for part in parts:
                i = 0
                for part in parts:
                    p = multiprocessing.Process(target=_set_conf_process, args=[i, part, all_args, return_dict])
                    p.start()
                    process.append(p)
                    i += 1
            # синхронизация с main процессом
            for p in process:
                p.join()

        # Получение конфигов с сервера
        else:
            all_hosts = zabbix_connection.get_host_list()
            all_hosts_count = len(all_hosts)
            parts = zabbix_connection.get_part_hosts(all_hosts, threads_count)
            i = 0
            process = []
            for part in parts:
                p = multiprocessing.Process(target=_get_conf_process, args=[i, part, all_args, return_dict])
                p.start()
                process.append(p)
                i += 1
            # синхронизация с main процессом
            for p in process:
                p.join()
        git_interractor = GitInterractor()
        git_interractor.call_git(all_args["saving_dir"], all_args)

        # Вывод времени работы программы
        end_time = datetime.now()
        total_time = end_time - start_time
        time_measurement = app_cli.TimeMeasurement(total_time)
        served_count = _get_served_hosts_count(return_dict)
        app_cli.write_log_file(all_args["log"], "SUCCESSFUL SERVED: "+str(served_count)+"/"+str(all_hosts_count)+" hosts in " + str(threads_count)+" Threads")
        app_cli.write_log_file(all_args["log"], time_measurement.__str__())
        app_cli.write_log_file(all_args["log"], "#" * 5 + " SESSION END " + "#" * 5)
    except KeyboardInterrupt as e:
        end_time = datetime.now()
        total_time = end_time - start_time
        time_measurement = app_cli.TimeMeasurement(total_time)
        served_count = _get_served_hosts_count(return_dict)
        app_cli.write_log_file(all_args["log"], "SUCCESSFUL SERVED: "+str(served_count)+"/"+str(all_hosts_count)+" hosts in " + str(threads_count)+" Threads")
        app_cli.write_log_file(all_args["log"], time_measurement.__str__())
        app_cli.write_log_file(all_args["log"], "#" * 5 + " SESSION STOPPED BY USER" + "#" * 5)
        

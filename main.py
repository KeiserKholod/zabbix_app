import zabbix_app.app_cli as app_cli
from zabbix_app.zabbix_base import ZabbixObject
from zabbix_app.config_getter import ZabbixConfigGetter

if __name__ == '__main__':
    threads_count = 1

    init_args_parser = app_cli.InitArgsParser()
    all_args = init_args_parser.get_all_args()
    print(all_args)
    zabbix_connection = ZabbixObject(all_args)
    print("Zabbix version: " + zabbix_connection.z_version["result"])
    all_hosts = zabbix_connection.get_host_list()
    # print(all_hosts)
    parts = zabbix_connection.get_part_hosts(all_hosts, threads_count)
    # print("all hosts count: " + str(len(all_hosts)))
    for part in parts:
        conf_getter = ZabbixConfigGetter(part, all_args)
        conf_getter.get_all_objects_configs()
        # print()
        # print("items: " + str(len(part)) + " " + part.__str__())
        conf_getter.write_configs_on_disk()

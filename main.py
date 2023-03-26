import zabbix_app.app_cli as app_cli
from zabbix_app.zabbix_base import ZabbixObject

if __name__ == '__main__':
    init_args_parser = app_cli.InitArgsParser()
    all_args = init_args_parser.get_all_args()
    print(all_args)
    zabbix_connection = ZabbixObject(all_args)
    print(zabbix_connection.z_version["result"])
    print(zabbix_connection.host_list)

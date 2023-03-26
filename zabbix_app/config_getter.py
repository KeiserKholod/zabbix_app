from pyzabbix import ZabbixAPI
from zabbix_base import *


class ZabbixConfigGetter:
    def __init__(self, zabbix_object: ZabbixObject):
        self.all_hosts = zabbix_object.get_host_list()

    def get_all_objects_configs(self):
        for host in self.all_hosts:
            self.get_host_config(host)

    def get_host_config(self, host):
        pass

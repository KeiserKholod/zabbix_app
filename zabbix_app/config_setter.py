import copy
import json
import os

from pyzabbix import ZabbixAPI

from zabbix_app.zabbix_base import ZabbixObject, ZabbixHost


class ZabbixConfigSetter:
    def __init__(self, host_list: list, args: dict):
        self.zabbix_obj = ZabbixObject(args)
        self.root = args["saving_dir"]
        self.hosts_to_change = host_list

    def get_data_from_file(self, hostname: str):
        zab_host = ZabbixHost()
        path = "".join([self.root, "hosts\\", hostname, "\\"])
        hostf = "".join([path, "host.conf"])
        templatesf = "".join([path, "templates.conf"])
        macrosf = "".join([path, "macros.conf"])
        itemsf = "".join([path, "items.conf"])
        groupsf = "".join([path, "groups.conf"])
        interfacesf = "".join([path, "interfaces.conf"])
        with open(hostf, "r") as file:
            zab_host.host = file.read()
        with open(groupsf, "r") as file:
            zab_host.groups = file.read()
        with open(interfacesf, "r") as file:
            zab_host.interfaces = file.read()
        with open(templatesf, "r") as file:
            zab_host.templates = file.read()
        with open(macrosf, "r") as file:
            zab_host.macros = file.read()
        with open(itemsf, "r") as file:
            zab_host.non_templates_items = file.read()
            # переделать на построчное
        return zab_host

    def set_config_for_all(self):
        for hostname in self.hosts_to_change:
            zab_host = self.get_data_from_file(hostname)
            print(zab_host)
            self.set_config(zab_host)

    def set_config(self, zab_host: ZabbixHost):
        pass

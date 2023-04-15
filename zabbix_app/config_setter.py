import copy
import json
import os
from threading import Thread
from multiprocessing import Process
from pyzabbix import ZabbixAPI
import time

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
            host_json = file.read()
            host_all = json.loads(host_json)
            zab_host.host = host_all["host"]
            zab_host.hostid = host_all["hostid"]
            zab_host.name = host_all["name"]
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

    def upd_config_for_all(self):
        for hostname in self.hosts_to_change:
            zab_host = self.get_data_from_file(hostname)
            print(zab_host.host)
            self.upd_config(zab_host)

    def upd_config(self, zab_host: ZabbixHost):
        base = self.zabbix_obj.zabbix_api.do_request('host.update',
                                                     {"hostid": zab_host.hostid, "name": zab_host.name,
                                                      "host": zab_host.host})
        interfaces_list = json.loads(zab_host.interfaces)
        # необходимо передавать обьект; json не ест
        interfaces = self.zabbix_obj.zabbix_api.do_request('host.update',
                                                           {"hostid": zab_host.hostid,
                                                            "interfaces": interfaces_list})
        groups_list = json.loads(zab_host.groups)
        groups = self.zabbix_obj.zabbix_api.do_request('host.update',
                                                       {"hostid": zab_host.hostid,
                                                        "groups": groups_list})
        templates_list = json.loads(zab_host.templates)
        templates = self.zabbix_obj.zabbix_api.do_request('host.update',
                                                          {"hostid": zab_host.hostid,
                                                           "templates": templates_list})
        macros_list = json.loads(zab_host.macros)
        macros = self.zabbix_obj.zabbix_api.do_request('host.update',
                                                       {"hostid": zab_host.hostid,
                                                        "macros": macros_list})

        #  так как некоторые обьекты read-only и нет программной возможности проверки - приходится отправлять поштучно
        # на один хост уходит около минуты; сильно грузится заббикс
        items_list = json.loads(zab_host.non_templates_items)
        for item in items_list:
            for key in item.keys():
                if not key == "itemid":
                    try:
                        p = Process(target=self.zabbix_obj.zabbix_api.do_request, args=['item.update',
                                                                                        {"itemid": item["itemid"],
                                                                                         key: item[key]}])
                        p.run()
                        # time.sleep(0.1)
                        # self.zabbix_obj.zabbix_api.do_request('item.update',
                        #                                       {"itemid": item["itemid"], key: item[key]})
                    except Exception as e:
                        print(e)

        # for item in items_list:
        #     try:
        #         self.zabbix_obj.zabbix_api.do_request('item.update',
        #                                               item)
        #     except Exception as e:
        #         pass

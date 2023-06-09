import json
import os
from threading import Thread

from zabbix_app import app_cli
from zabbix_app.config_getter import ZabbixConfigGetter
from zabbix_app.zabbix_base import ZabbixObject, ZabbixHost


class ZabbixConfigSetter:
    """Класс обьекта для записи конфигураций на сервер"""

    def __init__(self, host_list: list, args: dict):
        self.zabbix_obj = ZabbixObject(args)
        self.root = args["saving_dir"]
        self.log_path = args["log"]
        self.args = args
        self.hosts_to_change = host_list
        self.err_lvl = 0
        self.served = 0

    def do_log(self, zab_host):
        if self.err_lvl == 0:
            self.served += 1
            app_cli.write_log_file(self.log_path, "OK UPDATING: " + zab_host.host)
        else:
            app_cli.write_log_file(self.log_path, "ERROR UPDATING: " + zab_host.host)
        self.err_lvl = 0

    def get_data_from_file(self, hostname: str):
        zab_host = ZabbixHost()
        path = os.path.join(self.root, 'hosts', hostname)
        hostf = os.path.join(path, "host.conf")
        templatesf = os.path.join(path, "templates.conf")
        macrosf = os.path.join(path, "macros.conf")
        itemsf = os.path.join(path, "items.conf")
        groupsf = os.path.join(path, "groups.conf")
        interfacesf = os.path.join(path, "interfaces.conf")
        with open(hostf, "r") as file:
            host_json = file.read()
            host_all = json.loads(host_json)
            zab_host.host = host_all["host"]
            # можно брать запросом с сервера. Тогда получится создавать хост с нуля только по его hostname
            # если хоста с именем нет, то создать
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
        try:
            for hostname in self.hosts_to_change:
                zab_host = self.get_data_from_file(hostname)
                _host = self.ping_host(zab_host)
                is_new = False
                if len(_host) == 0:
                    self.create_host(zab_host)
                    is_new = True
                self.upd_config(zab_host, is_new)
                z_host = ZabbixHost()
                z_host.host = zab_host.host
                z_host.name = zab_host.name
                z_host.hostid = zab_host.hostid
                conf_getter = ZabbixConfigGetter([z_host], self.args)
                conf_getter.get_all_objects_configs()
                conf_getter.write_configs_on_disk()
        except KeyboardInterrupt as e:
            pass

    def ping_host(self, zab_host: ZabbixHost):
        """Проверяет, существует ли хост"""
        raw_list = self.zabbix_obj.zabbix_api.do_request('host.get', {"output": ["hostid", "host"],
                                                                      "filter": {"host": zab_host.host}})["result"]
        return raw_list

    def create_host(self, zab_host: ZabbixHost):
        """Создание хоста по файлу конфигурации"""
        groups_list = json.loads(zab_host.groups)
        interfaces_list = json.loads(zab_host.interfaces)
        for interface in interfaces_list:
            interface.pop("interfaceid")
            interface.pop("hostid")
        _host = {"host": zab_host.host, "name": zab_host.name, "groups": groups_list, "interfaces": interfaces_list}
        resp = self.zabbix_obj.zabbix_api.do_request('host.create', _host)["result"]
        zab_host.hostid = resp["hostids"][0]
        zab_host.non_templates_items = json.loads(zab_host.non_templates_items)
        for item in zab_host.non_templates_items:
            item["hostid"] = zab_host.hostid

        app_cli.write_log_file(self.log_path,
                               "HOST CREATED: host=" + zab_host.host + "; hostid= " + zab_host.hostid)

    def upd_config(self, zab_host: ZabbixHost, is_new):
        """Обновление конфигурации айтема"""

        if not is_new:
            # основные параметры: name, host
            base = self.zabbix_obj.zabbix_api.do_request('host.update',
                                                         {"hostid": zab_host.hostid, "name": zab_host.name,
                                                          "host": zab_host.host})
            # интерфейсы
            interfaces_list = json.loads(zab_host.interfaces)
            cg = ZabbixConfigGetter([zab_host], self.args)
            cg._get_host_interfaces(zab_host)
            _interfaces = cg.current_hosts[0].interfaces

            for interface in interfaces_list:
                if interface not in _interfaces:
                    interface.pop("interfaceid")
                    interface.pop("hostid")

            interfaces = self.zabbix_obj.zabbix_api.do_request('host.update',
                                                               {"hostid": zab_host.hostid,
                                                                "interfaces": interfaces_list})["result"]
            # группы
            groups_list = json.loads(zab_host.groups)
            groups = self.zabbix_obj.zabbix_api.do_request('host.update',
                                                           {"hostid": zab_host.hostid,
                                                            "groups": groups_list})
        # шаблоны
        templates_list = json.loads(zab_host.templates)
        templates = self.zabbix_obj.zabbix_api.do_request('host.update',
                                                          {"hostid": zab_host.hostid,
                                                           "templates": templates_list})
        # макросы
        macros_list = json.loads(zab_host.macros)
        macros = self.zabbix_obj.zabbix_api.do_request('host.update',
                                                       {"hostid": zab_host.hostid,
                                                        "macros": macros_list})
        # айтемы
        self._upd_or_create_item(zab_host)

        # логирование
        self.do_log(zab_host)

    def _upd_or_create_item(self, zab_host):
        """ Поочередная отправка параметров айтема для обновления. Для избегания ошибок их обнаружения.
         Если айтема не существует, то он создается."""
        items_list = zab_host.non_templates_items
        if type(zab_host.non_templates_items) is str:
            items_list = json.loads(zab_host.non_templates_items)
        for item in items_list:
            exist = True
            try:
                # проверка, существует ли айтем
                get_item = self.zabbix_obj.zabbix_api.do_request('item.get',
                                                                 {"output": "itemid", "itemids": item["itemid"]})[
                    "result"]
                if len(get_item) == 0:
                    exist = False
                    # создаем айтем, если его не существовало
                    create_item = self.zabbix_obj.zabbix_api.do_request("item.create", item)["result"]
                    self.write_log_file("ITEM CREATED: " + item["name"] + " FROM HOST: " + zab_host.host)
            except Exception as e:
                print(e)
                self.err_lvl += 1
            if exist:
                for key in item.keys():
                    if not key == "itemid":
                        try:
                            self.zabbix_obj.zabbix_api.do_request("item.update",
                                                                  {"itemid": item["itemid"],
                                                                   key: item[key]})["result"]
                        except Exception as e:
                            print(e)
                            self.err_lvl += 1

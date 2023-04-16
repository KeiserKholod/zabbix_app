import json
import os
from zabbix_app.zabbix_base import ZabbixObject, ZabbixHost
from collections import OrderedDict


class ZabbixConfigGetter:
    """Класс обьекта для получения конфигураций с сервера"""

    def __init__(self, host_list: list, args: dict):
        self.current_hosts = host_list
        self.zabbix_obj = ZabbixObject(args)
        self.root = args["saving_dir"]

    def get_all_objects_configs(self):
        """Получение шаблонов, групп, макросов, интерфейсов, не наследуемых, не discovered айтемов"""
        for host in self.current_hosts:
            self._get_host_templates(host)
            self._get_host_groups(host)
            self._get_host_macros(host)
            self._get_host_interfaces(host)
            self._get_host_items(host)

    def write_configs_on_disk(self):
        """Запись конфигураций в файлы на диск"""
        for host in self.current_hosts:
            path = os.path.join(self.root, 'hosts', host.host)
            os.makedirs(path, exist_ok=True)
            hostf = os.path.join(path, "host.conf")
            templatesf = os.path.join(path, "templates.conf")
            macrosf = os.path.join(path, "macros.conf")
            itemsf = os.path.join(path, "items.conf")
            groupsf = os.path.join(path, "groups.conf")
            interfacesf = os.path.join(path, "interfaces.conf")
            with open(hostf, "w+") as file:
                result = {"host": host.host, "name": host.name, "hostid": host.hostid}
                result = OrderedDict(sorted(result.items()))
                file.write(json.dumps(result, indent=3))
            with open(groupsf, "w+") as file:
                result = host.groups
                file.write(json.dumps(result, indent=4))
            with open(interfacesf, "w+") as file:
                result = host.interfaces
                file.write(json.dumps(result, indent=4))
            with open(templatesf, "w+") as file:
                result = host.templates
                file.write(json.dumps(result, indent=4))
            with open(macrosf, "w+") as file:
                result = host.macros
                file.write(json.dumps(result, indent=4))
            with open(itemsf, "w+") as file:
                result = host.non_templates_items
                file.write(json.dumps(result, indent=4))

    def _get_host_templates(self, host: ZabbixHost):
        """Получение шаблонов хоста"""
        templates_raw = self.zabbix_obj.zabbix_api.do_request('host.get',
                                                              {"output": "hostid",
                                                               "selectParentTemplates": ["templateid", "name"],
                                                               "hostids": host.hostid})["result"]
        _temp = templates_raw[0]["parentTemplates"]
        templates = []
        for t in _temp:
            t = OrderedDict(sorted(t.items()))
            templates.append(t)
        host.templates = templates

    def _get_host_groups(self, host: ZabbixHost):
        """Получение групп хоста"""
        groups_raw = self.zabbix_obj.zabbix_api.do_request('host.get',
                                                           {"output": "hostid",
                                                            "selectGroups": "extend",
                                                            "filter": {"hostid": host.hostid}})["result"]
        # ["name", "groupid"]
        _groups = groups_raw[0]["groups"]
        groups = []
        for g in _groups:
            g = OrderedDict(sorted(g.items()))
            groups.append(g)
        host.groups = groups

    def _get_host_macros(self, host: ZabbixHost):
        """Получение макросов хоста"""
        macros_raw = self.zabbix_obj.zabbix_api.do_request('host.get',
                                                           {"output": "hostid",
                                                            "selectMacros": "extend",
                                                            "filter": {"hostid": host.hostid}})["result"]
        _macros = macros_raw[0]
        macros = []
        if _macros.keys().__contains__("macros"):
            _macros = _macros["macros"]
            for macro in _macros:
                macros.append(OrderedDict(sorted(macro.items())))
            host.macros = macros

    def _get_host_interfaces(self, host: ZabbixHost):
        """Получение интерфейсов хоста"""
        interfaces_raw = self.zabbix_obj.zabbix_api.do_request('host.get',
                                                               {"output": "hostid",
                                                                "selectInterfaces": "extend",
                                                                "filter": {"hostid": host.hostid}})["result"]
        _interfaces = interfaces_raw[0]
        interfaces = []
        if _interfaces.keys().__contains__("interfaces"):
            _interfaces = _interfaces["interfaces"]
            for i in _interfaces:
                interfaces.append(OrderedDict(sorted(i.items())))
            host.interfaces = interfaces

    def _get_host_items(self, host: ZabbixHost):
        """Получение айтемов хоста. Не наследуемых от шаблона и не discovered."""
        readonly_params = ["error", "flags", "lastclock", "lastns", "lastvalue", "prevvalue",
                           "state", "templateid"]
        items_raw = self.zabbix_obj.zabbix_api.do_request('item.get',
                                                          {"output": "extend",
                                                           "hostids": host.hostid})["result"]
        items = []
        for item in items_raw:
            if item.keys().__contains__("templateid"):
                if item["templateid"] == "0":
                    _discovery_resp = self.zabbix_obj.zabbix_api.do_request('item.get',
                                                                            {"output": "parent_itemid",
                                                                             "itemids": item["itemid"],
                                                                             "selectItemDiscovery": ["parent_itemid"]})[
                        "result"][0]
                    # если есть родительский обьект, то это discovered item - пропускаем
                    if (len(_discovery_resp["itemDiscovery"]) != 0):
                        continue
                    _item = dict()
                    for key in item.keys():
                        if not (key in readonly_params):
                            _item[key] = item[key]
                    _item = OrderedDict(sorted(_item.items()))
                    items.append(_item)
        host.non_templates_items = items

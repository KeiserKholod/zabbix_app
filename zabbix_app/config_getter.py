import json
import os
from zabbix_app.zabbix_base import ZabbixObject, ZabbixHost


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
        for t in templates_raw:
            host.templates = t["parentTemplates"]

    def _get_host_groups(self, host: ZabbixHost):
        """Получение групп хоста"""
        groups_raw = self.zabbix_obj.zabbix_api.do_request('host.get',
                                                           {"output": "hostid",
                                                            "selectGroups": "extend",
                                                            "filter": {"hostid": host.hostid}})["result"]
        # ["name", "groupid"]
        for g in groups_raw:
            host.groups = g["groups"]

    def _get_host_macros(self, host: ZabbixHost):
        """Получение макросов хоста"""
        macros_raw = self.zabbix_obj.zabbix_api.do_request('host.get',
                                                           {"output": "hostid",
                                                            "selectMacros": "extend",
                                                            "filter": {"hostid": host.hostid}})["result"]
        for m in macros_raw:
            if m.keys().__contains__("macros"):
                host.macros = m["macros"]

    def _get_host_interfaces(self, host: ZabbixHost):
        """Получение интерфейсов хоста"""
        interfaces_raw = self.zabbix_obj.zabbix_api.do_request('host.get',
                                                               {"output": "hostid",
                                                                "selectInterfaces": "extend",
                                                                "filter": {"hostid": host.hostid}})["result"]
        for i in interfaces_raw:
            if i.keys().__contains__("interfaces"):
                host.interfaces = i["interfaces"]

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
                    items.append(_item)
        host.non_templates_items = items

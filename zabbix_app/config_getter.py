import copy

from pyzabbix import ZabbixAPI

from zabbix_app.zabbix_base import ZabbixObject, ZabbixHost


class ZabbixConfigGetter:
    def __init__(self, host_list: list, args: dict):
        self.current_hosts = host_list
        self.zabbix_obj = ZabbixObject(args)

    def get_all_objects_configs(self):
        for host in self.current_hosts:
            self._get_host_templates(host)
            self._get_host_groups(host)
            self._get_host_macros(host)

    def _get_host_templates(self, host: ZabbixHost):
        templates_raw = self.zabbix_obj.zabbix_api.do_request('host.get',
                                                              {"output": "hostid",
                                                               "selectParentTemplates": ["templateid", "name"],
                                                               "hostids": host.hostid})["result"]
        for t in templates_raw:
            host.templates = t["parentTemplates"]

    def _get_host_groups(self, host: ZabbixHost):
        groups_raw = self.zabbix_obj.zabbix_api.do_request('host.get',
                                                           {"output": "hostid",
                                                            "selectGroups": ["name", "groupid"],
                                                            "filter": {"hostid": host.hostid}})["result"]
        for g in groups_raw:
            host.groups = g["groups"]

    def _get_host_macros(self, host: ZabbixHost):
        macros_raw = self.zabbix_obj.zabbix_api.do_request('host.get',
                                                           {"output": "hostid",
                                                            "selectMacros": "extend",
                                                            "filter": {"hostid": host.hostid}})["result"]
        for m in macros_raw:
            if m.keys().__contains__("macros"):
                host.macros = m["macros"]

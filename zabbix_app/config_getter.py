import json
import os

from zabbix_app import app_cli
from zabbix_app.zabbix_base import ZabbixObject, ZabbixHost
from collections import OrderedDict


class ZabbixConfigGetter:
    """Класс обьекта для получения конфигураций с сервера"""

    def __init__(self, host_list: list, args: dict):
        self.current_hosts = host_list
        self.zabbix_obj = ZabbixObject(args)
        self.root = args["saving_dir"]
        self.err_lvl = 0
        self.log_path = args["log"]
        self.served = 0

    def do_log(self, zab_host):
        if self.err_lvl == 0:
            self.served += 1
            app_cli.write_log_file(self.log_path, "OK GET: " + zab_host.host)
        else:
            app_cli.write_log_file(self.log_path, "ERROR GET: " + zab_host.host)
        self.err_lvl = 0

    def get_all_objects_configs(self):
        """Получение шаблонов, групп, макросов, интерфейсов, не наследуемых, не discovered айтемов"""
        try:
            for host in self.current_hosts:
                self.get_simple_params(host)
                self._get_host_templates(host)
                self._get_host_groups(host)
                self._get_host_macros(host)
                self._get_host_interfaces(host)
                self._get_host_items(host)
                self.write_single_config_on_disk(host)
                self.do_log(host)
        except KeyboardInterrupt as e:
            pass


    def write_configs_on_disk(self):
        """Запись конфигураций в файлы на диск"""
        #templates_raw = json.dumps(templates_raw, indent=4, ensure_ascii=False).encode('utf8').decode()
        for host in self.current_hosts:
            self.write_single_config_on_disk(host)
                
    def write_single_config_on_disk(self, host):
        """Запись конфигураций одного хоста в файл"""
        tmp = OrderedDict(sorted({"host": host.host, "name": host.name, "hostid": host.hostid, "status":host.status, "description":host.description, "proxy_hostid":host.proxy_hostid}.items()))
        conf_datas = [("host.conf", tmp),
        ("templates.conf", host.templates),
        ("macros.conf", host.macros),
        ("items.conf", host.non_templates_items),
        ("groups.conf", host.groups),
        ("interfaces.conf", host.interfaces)]
        path_d = os.path.join(self.root, 'hosts', host.host)
        os.makedirs(path_d, exist_ok=True)
        #print(path_d)
        for conf_data in conf_datas:
            path_f = os.path.join(path_d, conf_data[0])
            #print(path_f)
            with open(path_f, "w+") as file:
                file.write(json.dumps(conf_data[1], indent=4, ensure_ascii=False).encode('utf8').decode())    

    def _get_host_templates(self, host: ZabbixHost):
        """Получение шаблонов хоста"""
        try:
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
        except Exception as e:
            self.err_lvl += 1
            print(e)
            return 0
            
            
            
    def get_simple_params(self, host: ZabbixHost):
        """description, proxy hostid, status"""
        try:
            data_raw = self.zabbix_obj.zabbix_api.do_request('host.get',
                                                                {"output": ["hostid",
                                                                 "description",
                                                                 "status",
                                                                 "proxy_hostid"],
                                                                 "filter": {"hostid": host.hostid}})["result"]
            host.status = data_raw[0]["status"]
            host.description = data_raw[0]["description"]
            host.proxy_hostid = data_raw[0]["proxy_hostid"]
        except Exception as e:
            self.err_lvl += 1
            print(e)
            return 0
        

    def _get_host_groups(self, host: ZabbixHost):
        """Получение групп хоста"""
        try:
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
            if(len(groups) == 0):
                self.err_lvl += 1
                print(groups_raw)
        except Exception as e:
            self.err_lvl += 1
            print(e)
            return 0

    def _get_host_macros(self, host: ZabbixHost):
        try:
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
        except Exception as e:
            self.err_lvl += 1
            print(e)
            return 0

    def _get_host_interfaces(self, host: ZabbixHost):
        """Получение интерфейсов хоста"""
        try:
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
        except Exception as e:
            self.err_lvl += 1
            print(e)
            return 0

    def _get_host_items(self, host: ZabbixHost):
        """Получение айтемов хоста. Не наследуемых от шаблона и не discovered."""
        try:
            readonly_params = ["error", "flags", "lastclock", "lastns", "lastvalue", "prevvalue",
                               "state", "templateid"]
            _items_disc = self.zabbix_obj.zabbix_api.do_request('item.get',
                                                              {"output": "extend",
                                                               "hostids": host.hostid,"inherited" : False, "templated" : False,"discovered" : False,
                                                                                 "selectItemDiscovery": [
                                                                                     "parent_itemid"]})["result"]
            items = []
            for item in _items_disc:
                # если есть родительский обьект, то это discovered item - пропускаем
                if (len(item["itemDiscovery"]) != 0):
                    continue
                _item = dict()
                for key in item.keys():
                    if not (key in readonly_params):
                        _item[key] = item[key]
                _item = OrderedDict(sorted(_item.items()))
                items.append(_item)
            host.non_templates_items = items
        except Exception as e:
            self.err_lvl += 1
            print(e)
            return 0

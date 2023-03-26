from pyzabbix.api import ZabbixAPI


class ZabbixObject:
    def __init__(self, args: dict):
        self._args = args
        self.zabbix_api = self._init_connection()
        self.z_version = self.get_zabbix_version()
        self.host_list = self.get_host_list()

    def get_zabbix_version(self):
        try:
            return self.zabbix_api.do_request('apiinfo.version')
        except Exception as e:
            raise e

    def get_host_list(self):
        host_list = []
        raw_list = None
        try:
            raw_list = self.zabbix_api.do_request('host.get', {"output": ["host", "name"]})["result"]
        except Exception as e:
            raise e
        for host_dict in raw_list:
            host = ZabbixHost()
            host.host = host_dict['host']
            host.name = host_dict['name']
            host.hostid = host_dict['hostid']
            host_list.append(host)
        return host_list

    def _init_connection(self):
        try:
            return ZabbixAPI(url=self._args['link'], user=self._args['login'], password=self._args['pass'])
        except Exception as e:
            raise e


class ZabbixHost:
    def __init__(self):
        self.name = ""
        self.hostid = ""
        self.host = ""
        self.groups = []
        self.macros = []
        self.templates = []
        self.non_templates_items = []

    def __str__(self):
        return "name: '{}'; host: '{}'; hostid: '{}'; groups: {}; macros: {}; templates: {}; non templates items: {}".format(
            self.name, self.host, self.hostid, self.groups, self.macros,
            self.templates, self.non_templates_items)

    def __repr__(self):
        return self.__str__()

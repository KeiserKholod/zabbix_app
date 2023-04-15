from pyzabbix.api import ZabbixAPI


class ZabbixObject:
    """Класс обьекта для взаимодействия сервером  Zabbix"""

    def __init__(self, args: dict):
        self._args = args
        self.zabbix_api = self._init_connection()
        self.z_version = self.get_zabbix_version()

    def get_zabbix_version(self):
        """Получение версии подключенного Zabbix сервера"""
        try:
            return self.zabbix_api.do_request('apiinfo.version')
        except Exception as e:
            raise e

    def get_host_list(self):
        """Получение списка обьектов класса ZabbixHost с name, hostid, host хоста"""
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
        """Подключение к серверу Zabbix"""
        try:
            return ZabbixAPI(url=self._args['link'], user=self._args['login'], password=self._args['pass'])
        except Exception as e:
            raise e

    def get_part_hosts(self, all_hosts: list, threads_count):
        """Функция для разделения списка всех хостов на равные по размеру подгруппы для многопоточной работы"""
        parts = []
        len_all = len(all_hosts)
        part_len = len_all // threads_count
        iteration = 1
        _exit = False
        for i in range(0, len_all, part_len):
            max_num = i + part_len
            if (max_num > len_all) or (iteration == threads_count):
                max_num = len_all
                _exit = True
            part = all_hosts[i:max_num]
            parts.append(part)
            iteration += 1
            if _exit:
                break
        return parts


class ZabbixHost:
    """Обьект для хранения информации о хосте"""

    def __init__(self):
        self.name = ""
        self.hostid = ""
        self.host = ""
        self.groups = []
        self.macros = []
        self.templates = []
        self.interfaces = []
        self.non_templates_items = []

    def __str__(self):
        return "name: '{}'; host: '{}'; hostid: '{}'; groups: {}; macros: {}; templates: {}; interfaces: {}; non templates items: {}".format(
            self.name, self.host, self.hostid, self.groups, self.macros,
            self.templates, self.interfaces, self.non_templates_items)

    def __repr__(self):
        return self.__str__()

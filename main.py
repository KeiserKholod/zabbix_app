import zabbix_app.app_cli as app_cli

if __name__ == '__main__':
    init_args_parser = app_cli.InitArgsParser()
    all_args = init_args_parser.get_all_args()
    print(all_args)

import os
import subprocess

from zabbix_app import app_cli


class GitInterractor:
    """Класс для взаимодействия с GIT"""

    def __init__(self):
        pass

    def call_git(self, path_to_dir, all_args):
        """Вся работа с гитом"""
        current_dir = os.getcwd()

        os.chdir(path_to_dir)
        answ = subprocess.run(["git", "status"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        answ = answ.stdout.decode("utf-8")
        answ = answ.__str__().lower()
        if answ.find("not a git repository") > -1 or answ.find("не найден") > -1:
            app_cli.write_log_file(all_args["log"], "GIT: Creating git-repo")
            answ = subprocess.run(["git", "init"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            answ = answ.stdout.decode("utf-8")
            answ = answ.__str__().lower()

            if answ.find("initialized") > -1 or answ.find("инициализирован") > -1:
                os.chdir(current_dir)
                app_cli.write_log_file(all_args["log"], "GIT: Repo initialized in " + path_to_dir)
                os.chdir(path_to_dir)

        answ = subprocess.run(["git", "status"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        answ = answ.stdout.decode("utf-8")
        answ = answ.__str__().lower()
        if answ.find("untracked files present") > -1 or answ.find("неотслеживаемые файлы") > -1 or answ.find(
                "changes not staged for commit") > -1:
            answ = subprocess.run(["git", "add", "*"], stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
            answ = answ.stdout.decode("utf-8")
            answ = answ.__str__().lower()
            answ = subprocess.run(["git", "commit", "-m", '"message"'], stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
            answ = answ.stdout.decode("utf-8")
            answ = answ.__str__().lower()
            os.chdir(current_dir)
            app_cli.write_log_file(all_args["log"], "GIT: Commit created")
            os.chdir(path_to_dir)
        else:
            os.chdir(current_dir)
            app_cli.write_log_file(all_args["log"], "GIT: nothing to commit")
            os.chdir(path_to_dir)

        os.chdir(current_dir)

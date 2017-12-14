"""
Linuxイメージを利用した軽量コンテナ

予めLinuxのroot以下を任意のディレクトリに用意して、実行したいアプリケーションを
指定すると任意のディレクトリ以下をchroot軽量コンテナとして起動してその中で
アプリケーションを実行する。
"""
import pathlib
import os
import shutil
import subprocess
from multiprocessing import Process


class Jail:
    """
    隔離実行環境のLinuxイメージに関するデータを格納する.
    """
    def __init__(self, jail_path, exec_path="/app"):
        self.jail_path = pathlib.Path(jail_path).resolve() # Linux image
        self.exec_path = pathlib.Path( # Linux image内でアプリケーションを実行するディレクトリまでの相対パス
            exec_path if exec_path[0] != '/' else exec_path[1:]
        )
        _path = self.jail_path / self.exec_path # ホストOSから見た `exec_path`
        if not _path.exists():
            default_umask = os.umask(0)
            _path.mkdir(mode=0o755)
            os.chown(_path, '1000', '1000')
            os.umask(default_umask)


def jailing(jail, prisoner, *args):
    if type(jail) is not Jail:
        raise ValueError("`jail` must be Jail.")
    prisoner = pathlib.Path(prisoner)
    if pathlib.Path(prisoner).is_dir():
        shutil.copytree(prisoner, jail.jail_path / jail.exec_path / prisoner)
    else:
        shutil.copy2(prisoner, jail.jail_path / jail.exec_path)
    jail_p = Process(target=run, args=(jail.jail_path, jail.exec_path, *args))
    jail_p.start()
    jail_p.join()


def run(jail_path, exec_path, *args):
    os.chroot(jail_path)
    os.chdir('/')
    os.chdir(exec_path)
    subprocess.run(*args)


if __name__ == '__main__':
    import tarfile
    root = pathlib.Path('pyjailroot')
    if not root.exists():
        root.mkdir()
        with tarfile.open('pyjail.tar.gz') as pyjail:
            pyjail.extractall(path=root)
        default_umask = os.umask(0)
        root.chmod(mode=0o755)
        os.umask(default_umask)

    j = Jail(root)
    jailing(j, 'app', ['python3', 'app/app.py'])

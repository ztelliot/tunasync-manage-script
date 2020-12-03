import json
import wget
import requests
import tarfile
import os
from configobj import ConfigObj
import delegator
import platform
import re

manager_conf = ConfigObj(list_values=False)
manager_conf.filename = '/etc/tunasync/manager.conf'
worker_conf = ConfigObj(list_values=False)
worker_conf.filename = '/etc/tunasync/worker.conf'
mirror_conf = ConfigObj(list_values=False)
ctl_conf = ConfigObj(list_values=False)
ctl_conf.filename = '/etc/tunasync/ctl.conf'
path = os.getcwd()


def get_config():
    with open('config.json', 'r') as rf:
        mir = rf.read()
    config = eval(mir)
    rf.close()
    return config


def ins_bin():
    try:
        plat = platform.machine()
        try:
            api = requests.get("https://api.github.com/repos/tuna/tunasync/releases/latest")
        except:
            api = requests.get(
                "https://cold-breeze-c026.h-wkfx4vqhcj-xsv.workers.dev/repos/tuna/tunasync/releases/latest")
            # 备用地址 https://github-api-indol.vercel.app/repos/tuna/tunasync/releases/latest
        releases = [asset['browser_download_url'] for asset in api.json()['assets']]
        url = ''
        for release in releases:
            if (plat == 'AMD64' or plat == 'x86_64') and 'amd' in release:
                url = release
            elif plat == "aarch64" and 'arm' in release:
                url = release
            else:
                print("Nonsupport Platform")
                return -1
        if url:
            print("Get download URL:" + url)
            try:
                filename = wget.download(url, 'tunasync-linux-bin.tar.gz')
                print("Download success")
            except:
                url = str(url).replace('github.com', 'g.ioiox.com/https://github.com')
                print("Try " + url)
                filename = wget.download(url, 'tunasync-linux-bin.tar.gz')
                print("Download success")
            try:
                archive = tarfile.open(filename)
                archive.extractall()
                archive.close()
                print("Unzip success")
                try:
                    os.remove(filename)
                except:
                    pass
                delegator.run("chmod +x tunasync tunasynctl")
                delegator.run("mv tunasync tunasynctl /usr/bin")
                delegator.run("mkdir -p /etc/tunasync/mirrors")
                return 1
            except:
                print("Unzip failed")
                try:
                    os.remove(filename)
                except:
                    pass
                return -1
        else:
            print("Get URL ERROR")
            return -1
    except:
        print("Get bin error")
        return -1


def init_manager():
    config = get_config()
    debug = input("是否开启Debug(Y/N)[N]")
    if debug.upper() == 'Y':
        manager_conf['debug'] = 'true'
    else:
        manager_conf['debug'] = 'false'
    bind_ip = input("绑定IP[127.0.0.1]：") or '127.0.0.1'
    addr = "\"" + bind_ip + "\""
    bind_port = input("绑定端口[14242]：") or '14242'
    manager_conf['server'] = {'addr': addr, 'port': bind_port}
    config['manager_save'] = {}
    config['manager_save']['url'] = bind_ip + ':' + bind_port
    with open('config.json', 'w') as cf:
        cf.write(json.dumps(config))
    cf.close()
    ssl_cert = '\"\"'
    ssl_key = '\"\"'
    manager_conf['server']['ssl_cert'] = ssl_cert
    manager_conf['server']['ssl_key'] = ssl_key
    db_type = "\"bolt\""
    db_file = "\"" + path + "/db/manager.db\""
    ca_cert = "\"\""
    manager_conf['files'] = {'db_type': db_type, 'db_file': db_file, 'ca_cert': ca_cert}
    try:
        os.mkdir('/etc/tunasync')
        os.mkdir('/etc/tunasync/mirrors')
    except:
        pass
    manager_conf.write()
    ctl_conf['manager_addr'] = "\"" + bind_ip + "\""
    ctl_conf['manager_port'] = bind_port
    ctl_conf.write()


def init_worker():
    config = get_config()
    name = input("输入Worker名称：")
    mirror_dir = input("输入放置镜像文件的目录：(以/结尾)[/data/mirrors/]") or '/data/mirrors/'
    con = input("输入线程数[10]：") or str(10)
    interval = input("输入全局同步周期(分)[1440]：") or '1440'
    worker_conf['global'] = {'name': "\"" + name + "\"", "log_dir": "\"" + path + "/logs/{{.Name}}\"",
                             'mirror_dir': "\"" + mirror_dir + "\"", 'concurrent': con, 'interval': interval}
    api = input("输入manager地址[http://" + config['manager_save']['url'] + "]：") or 'http://' + config['manager_save'][
        'url']
    token = input("输入token：")
    worker_conf['manager'] = {"api_base": "\"" + api + "\"", "token": "\"" + token + "\""}
    cgroup = input("是否开启cgroup(Y/N)[N]")
    if cgroup.upper() == 'Y':
        base_path = input("输入base_path：")
        group = input("输入group：")
        worker_conf['cgroup'] = {'enable': 'true', 'base_path': "\"" + base_path + "\"", 'group': "\"" + group + "\""}
    else:
        base_path = ""
        group = ""
        worker_conf['cgroup'] = {'enable': 'false', 'base_path': "\"" + base_path + "\"", 'group': "\"" + group + "\""}
    hostname = input("输入主机名[localhost]：") or 'localhost'
    ip = '127.0.0.1'
    listen_addr = input("绑定IP[" + ip + "]：") or ip
    listen_port = input("绑定端口[6000]：") or '6000'
    worker_conf['server'] = {'hostname': "\"" + hostname + "\"", 'listen_addr': "\"" + listen_addr + "\"",
                             'listen_port': listen_port}
    worker_conf['include'] = {'include_mirrors ': "\"/etc/tunasync/mirrors/*.conf\""}
    ssl_cert = '\"\"'
    ssl_key = '\"\"'
    worker_conf['server']['ssl_cert'] = ssl_cert
    worker_conf['server']['ssl_key'] = ssl_key
    worker_conf.write()
    config['manager_save']['worker'] = name
    config['manager_save']['path'] = worker_conf['global']['mirror_dir'][1:-1]
    with open('config.json', 'w') as cf:
        cf.write(json.dumps(config))
    cf.close()


def systemd():
    # 开始设置systemd
    print("终止Manager...")
    cmd = delegator.run("systemctl stop tunasync_manger")
    print(cmd.out)
    print("终止Worker...")
    cmd = delegator.run("systemctl stop tunasync_worker")
    print(cmd.out)
    delegator.run("cp -f systemd/tunasync_manager.service /etc/systemd/system/")
    delegator.run("cp -f systemd/tunasync_worker.service /etc/systemd/system/")
    print("重载...")
    c = delegator.run("systemctl daemon-reload")
    if c.return_code == 0:
        print("成功")


def systemd_control(action, mode):
    if mode == 'manager':
        return delegator.run("systemctl " + action + " tunasync_manager").out
    elif mode == 'worker':
        return delegator.run("systemctl " + action + " tunasync_worker").out


# 镜像管理
def ctl_control(action, mirror='', size=''):
    worker = get_config()['manager_save']['worker']
    actions = ['start', 'stop', 'disable', 'restart']
    if action == 'flush':
        command = "tunasynctl flush"
    elif action == 'set-size':
        command = "tunasynctl set-size -w " + worker + " " + mirror + " " + size
    elif action in actions:
        command = "tunasynctl " + action + " -w " + worker + " " + mirror
    elif action == 'reload':
        command = "tunasynctl reload -w " + worker
    else:
        return 0
    return delegator.run(command).out


class mirror(object):
    def __init__(self, name):
        with open('config.json', 'r') as rf:
            mir = rf.read()
        self.__config__ = eval(mir)
        rf.close()
        self.name = name

    def add(self):
        name = self.name
        mirror_conf.filename = '/etc/tunasync/mirrors/' + name + '.conf'
        provider = input("输入同步方式[rsync]：") or 'rsync'
        upstream = input("输入同步源(rsync方式的链接结尾必须为/)：")
        command = ''
        if provider == "command":
            command = '\"' + input("输入同步脚本位置(绝对路径)：") + '\"'
        elif provider == "rsync":
            rsync_options = "[\"--info=progress2\"]"
        else:
            pass
        interval = input("设置镜像同步周期(min)(留空沿用全局周期)：") or ''
        v6 = input("是否启用ipv6?(Y/N)[N]")
        if v6.upper() == 'Y':
            use_ipv6 = 'true'
        else:
            use_ipv6 = 'false'
        memory_limit = input("内存限制(不填不限制)：") or ''
        mirror = {"name": '\"' + name + '\"', "provider": '\"' + provider + '\"', "upstream": '\"' + upstream + '\"',
                  "use_ipv6": use_ipv6}
        if command:
            mirror['command'] = command
        if provider == "rsync":
            mirror['rsync_options'] = rsync_options
        if memory_limit:
            mirror['memory_limit'] = '\"' + memory_limit + '\"'
        if interval:
            mirror['interval'] = interval
        mirror_conf['[mirrors]'] = mirror
        self.__config__[name] = {'path': self.__config__['manager_save']['path'] + name, 'type': provider}
        mirror_conf.write()
        with open('config.json', 'w') as cf:
            cf.write(json.dumps(self.__config__))
        cf.close()
        print("重载Worker...")
        print(ctl_control('reload'))
        print("检测Worker状态...")
        status = systemd_control('status', 'worker')
        if 'active' in status and 'running' in status:
            pass
        else:
            print("Worker未启动\n", status)
            print("启动Worker...")
            systemd_control('start', 'worker')
            print("设置worker自启...")
            systemd_control('enable', 'worker')
        print("开始同步...")
        print(ctl_control('start', name))

    def delete(self):
        print("删除文件...")
        print(delegator.run(
            "rm -rf " + self.__config__[self.name]['path'] + ' /etc/tunasync/mirrors/' + self.name + '.conf').out)
        print("操作tunasync...")
        print(ctl_control('reload'))
        print(ctl_control('disable', self.name))
        print(ctl_control('flush'))
        self.__config__.pop(self.name)
        with open('config.json', 'w') as df:
            df.write(json.dumps(self.__config__))
        df.close()
        return 1

    def disable(self):
        print("禁用中...")
        print(ctl_control('disable', self.name))
        print(delegator.run("tunasynctl flush").out)
        return 1

    def enable(self):
        print("启用中...")
        print(ctl_control('start', self.name))
        delegator.run("tunasynctl flush")
        return 1

    def refresh(self):
        get_size = "`du -sh " + self.__config__[self.name]['path'] + " | awk '{print $1}'`"
        print(ctl_control('set-size', self.name, get_size))
        return 1

    def logs(self):
        log = path + "/logs/" + self.name + '/latest'
        print(delegator.run("tail -n 10 " + log).out)
        return 1

    def info(self):
        jobs = requests.get("http://" + self.__config__['manager_save']['url'] + "/jobs").text
        list = json.loads(jobs)
        size = 'NULL'
        status = 'NULL'
        for job in list:
            if job['name'] == self.name:
                last_begin_time = job['last_started_ts']
                last_time = job['last_ended_ts']
                next_time = job['next_schedule_ts']
                pass_time = str(last_time - last_begin_time)
                if int(pass_time) <= 0:
                    pass_time = '-'
                size = job['size']
                status = job['status']
                file_name = remain = speed = rate = total = chk_now = chk_remain = '-'
                if status == 'syncing':
                    logs = delegator.run('tail -5 ' + path + "/logs/" + self.name + '/latest').out.split("\n")
                    for log in logs:
                        if 'B/s' in log:
                            if 'xfr' in log:
                                chk = str(re.findall(r'[(](.*?)[)]', log)[0])
                                chk_now = re.findall(r'[#](.*?)[,]', chk)[0]
                                chk_remain = re.findall(r'[=](.*?)[/]', chk)[0]
                                total = chk.split("/")[1]
                            infos = log.split(" ")
                            for info in infos:
                                if '%' in info:
                                    rate = info
                                elif 'B/s' in info:
                                    speed = info
                                elif ':' in info:
                                    remain = info
                                elif '=' in info or '#' in info:
                                    pass
                                elif info:
                                    size = info
                        elif log:
                            files = log.split('/')
                            file_name = files[-1]
                    try:
                        return {'status': status, 'size': size, 'last_time': last_time, 'pass_time': pass_time,
                                'chk_now': chk_now, 'chk_remain': chk_remain, 'total': total, 'rate': rate,
                                'speed': speed, 'remain': remain, 'file_name': file_name,
                                'next_time': next_time}
                    except:
                        pass
                return {'status': status, 'size': size, 'last_time': last_time, 'pass_time': pass_time,
                        'next_time': next_time}

import json
import wget
import requests
import tarfile
import bz2
import os
from configobj import ConfigObj
import delegator
import distro
import platform
from crontab import CronTab
import re

manager_conf = ConfigObj(list_values=False)
manager_conf.filename = '/etc/tunasync/manager.conf'
worker_conf = ConfigObj(list_values=False)
worker_conf.filename = '/etc/tunasync/worker.conf'
mirror_conf = ConfigObj(list_values=False)
ctl_conf = ConfigObj(list_values=False)
ctl_conf.filename = '/etc/tunasync/ctl.conf'
path = os.getcwd()
manager_ssl = 0
with open('config.json', 'r') as rf:
    mir = rf.read()
config = eval(mir)
rf.close()
crontab = CronTab(user=True)


### Cron管理模块开始
def add_cron(command, time, name):
    job = crontab.new(command=command)
    job.setall(time)
    job.set_comment(name)
    crontab.write_to_user()


def del_cron(name):
    crontab.remove_all(comment=name)
    crontab.write_to_user()
### Cron管理模块结束


### 安装部分开始
def bin():
    try:
        try:
            res = requests.get("https://api.github.com/repos/tuna/tunasync/releases/latest")
        except:
            res = requests.get("https://api.git.sdut.me/repos/tuna/tunasync/releases/latest")
        dl_url = res.json()['assets'][0]['browser_download_url']
        if dl_url:
            print("Get download URL:" + dl_url)
            try:
                filename = wget.download(dl_url, 'tunasync-linux-bin.tar.bz2')
                print("Download success")
            except:
                dl_url = str(dl_url).replace('github.com', 'github.com.cnpmjs.org')
                print("Try " + dl_url)
                filename = wget.download(dl_url, 'tunasync-linux-bin.tar.bz2')
                print("Download success")
            try:
                archive = tarfile.open(filename, 'r:bz2')
                archive.debug = 1
                for tarinfo in archive:
                    archive.extract(tarinfo, r'.')
                archive.close()
                print("Unzip success")
                try:
                    os.remove(filename)
                except:
                    pass
                delegator.run("chmod +x tunasync tunasynctl")
                delegator.run("mv tunasync tunasynctl /usr/bin")
                return 1
            except:
                print("Unzip failed")
                try:
                    os.remove(filename)
                except:
                    pass
                return -1
        else:
            print("Get download URL error")
            return -1
    except:
        print("Get bin error")
        return -1


# 备用的方法
def go_bin():
    print("Install Go...")
    plat = platform.machine()
    print("当前处理器架构为" + plat)
    if plat == "x86_64":
        mode = 'amd64'
    elif plat == "i386":
        mode = '386'
    elif plat == "aarch64":
        mode = 'arm64'
    elif plat == "arm":
        choice = input("ARM 32位处理器有极大概率无法完成环境配置，是否继续(Y/N)")
        if choice == 'y' or choice == 'Y':
            pass
        else:
            print("终止环境配置...")
            return 0
        mode = 'armv6l'
    else:
        print("Unsupport CPU Type")
        return 0
    url = "https://golang.org/dl/go1.14.4.linux-" + mode + ".tar.gz"
    filename = 'go1.14.4.tar.gz'
    print("Golang download from:" + url)
    wget.download(url, filename)
    print("Start Untar")
    archive = tarfile.open(filename)
    archive.extractall(path='go_bin/')
    archive.close()
    print("Untar Succeed")
    delegator.run("cp -f go_bin/bin/* /usr/bin/")
    print("Install Golang Succeed")


# 改用软件包管理器配置
def go():
    print("Install Go...")
    like = distro.info()['like']
    print("当前系统为" + like)
    if like == "ubuntu":
        print("配置软件源...")
        cmd = delegator.run("add-apt-repository ppa:longsleep/golang-backports")
        if cmd.return_code == 0:
            print("成功")
        print("更新缓存...")
        cmd = delegator.run("apt update")
        if cmd.return_code == 0:
            print("完成")
        print("安装Golang...")
        cmd = delegator.run("apt install golang-go -y")
        if cmd.return_code == 0:
            print("安装完成")
        else:
            print("尝试使用二进制文件方式安装Golang...")
            go_bin()
    elif like.find("rhel") >= 0:
        print("安装epel...")
        cmd = delegator.run("yum install epel-release -y")
        if cmd.return_code == 0:
            print("成功")
        print("安装Golang...")
        cmd = delegator.run("yum install golang -y")
        if cmd.return_code == 0:
            print("安装完成")
    else:
        print("暂不支持的发行版...\n尝试使用二进制文件方式安装Golang...")
        go_bin()
    print("换用国内镜像源")
    delegator.run("go env -w GO111MODULE=on")
    delegator.run("go env -w GOPROXY=https://goproxy.cn,direct")


def dep():
    go()
    like = distro.info()['like']
    if like == "ubuntu":
        print("更新缓存...")
        cmd = delegator.run("apt update")
        if cmd.return_code == 0:
            print("完成")
        print("安装 git make...")
        cmd = delegator.run("apt install -y git make")
        if cmd.return_code == 0:
            print("安装完成")
    elif like.find("rhel") >= 0:
        print("安装 git make...")
        cmd = delegator.run("yum install git make -y")
        if cmd.return_code == 0:
            print("安装完成")
    else:
        print("暂不支持的发行版，请手动安装git make")
        # return 0


def build():
    dep()
    print("克隆项目")
    try:
        os.remove("tunasync")
    except:
        pass
    cmd = delegator.run("git clone https://github.com/tuna/tunasync.git")
    if cmd.return_code == 0:
        print("完成")
    print("开始编译")
    cmd = delegator.run("cd tunasync && make")
    if cmd.return_code == 0:
        print("编译完成")
    print("验证结果...")
    code = 1
    cmd = delegator.run("cd tunasync/build && ./tunasync -v")
    print(cmd.out)
    if cmd.return_code != 0:
        code = 0
    cmd = delegator.run("cd tunasync/build && ./tunasynctl -v")
    print(cmd.out)
    if cmd.return_code != 0:
        code = 0
    if code == 1:
        delegator.run("cp -f tunasync/build/* /usr/bin")
        print("验证完成")
        return 1
    else:
        print("失败")
        return -1
### 安装部分结束


### 基础设置部分开始
def ssl(mode, name=''):
    global manager_ssl
    if mode == 0:
        type = input("是否为manager设置SSL(Y/N)(N)")
        ssl_cert = '\"\"'
        ssl_key = '\"\"'
        if type == 'Y' or type == 'y':
            confirm = input("确认证书文件在ssl/manager目录下，并分别命名为ssl.pem ssl.key(Y/N)")
            if confirm == 'Y' or confirm == 'y':
                ssl_cert = "\"" + path + '/ssl/manager/ssl.pem\"'
                ssl_key = "\"" + path + '/ssl/manager/ssl.key\"'
                print("同时，别忘了将ca_cert也放置在ssl/manager目录下，并命名为ca.cert")
                manager_ssl = 1
            else:
                print("请放置好文件后重新配置")
        else:
            pass
        manager_conf['server']['ssl_cert'] = ssl_cert
        manager_conf['server']['ssl_key'] = ssl_key
    else:
        ssl_cert = '\"\"'
        ssl_key = '\"\"'
        if manager_ssl:
            worker_conf['manager']['ca_cert'] = "\"" + path + '/ssl/manager/ca.cert\"'
        type = input("是否为worker设置SSL(Y/N)(N)")
        if type == 'Y' or type == 'y':
            confirm = input("确认证书文件在ssl/worker目录下，并分别命名为" + name + "-ssl.pem " + name + "-ssl.key(Y/N)")
            if confirm == 'Y' or confirm == 'y':
                ssl_cert = "\"" + path + '/ssl/worker/' + name + '-ssl.pem\"'
                ssl_key = "\"" + path + '/ssl/worker/' + name + '-ssl.key\"'
            else:
                print("请放置好文件后重新配置")
        else:
            pass
        worker_conf['server']['ssl_cert'] = ssl_cert
        worker_conf['server']['ssl_key'] = ssl_key


# 暂不允许修改
def db():
    db_type = "\"bolt\""
    db_file = "\"" + path + "/db/manager.db\""
    ca_cert = "\"\""
    manager_conf['files'] = {'db_type': db_type, 'db_file': db_file, 'ca_cert': ca_cert}


def init_manager():
    debug = input("是否开启Debug(Y/N)(N)")
    if debug == 'Y' or debug == 'y':
        manager_conf['debug'] = 'true'
    else:
        manager_conf['debug'] = 'false'
    bind_ip = input("绑定IP(127.0.0.1)：")
    if bind_ip:
        pass
    else:
        bind_ip = '127.0.0.1'
    addr = "\"" + bind_ip + "\""
    bind_port = input("绑定端口(14242)：")
    if bind_port:
        pass
    else:
        bind_port = '14242'
    manager_conf['server'] = {'addr': addr, 'port': bind_port}
    config['manager_save'] = {}
    config['manager_save']['url'] = bind_ip + ':' + bind_port
    with open('config.json', 'w') as cf:
        cf.write(json.dumps(config))
    cf.close()
    ssl(0)
    db()
    try:
        os.mkdir('/etc/tunasync')
        os.mkdir('/etc/tunasync/mirrors')
    except:
        pass
    manager_conf.write()
    ctl_conf['manager_addr'] = "\"" + bind_ip + "\""
    ctl_conf['manager_port'] = bind_port
    if manager_ssl:
        ctl_conf["ca_cert"] = "\"" + path + '/ssl/manager/ca.cert\"'
    ctl_conf.write()


def init_worker():
    name = input("输入Worker名称：")
    dir = input("输入放置镜像文件的目录：(以/结尾)(/data/mirrors/)")
    if dir:
        pass
    else:
        dir = '/data/mirrors/'
    con = input("输入线程数(10)：")
    if con:
        pass
    else:
        con = str(10)
    interval = input("输入全局同步周期(分)(1440)：")
    if interval:
        pass
    else:
        interval = '1440'
    worker_conf['global'] = {'name': "\"" + name + "\"", "log_dir": "\"" + path + "/logs/{{.Name}}\"", 'mirror_dir': "\"" + dir + "\"", 'concurrent': con, 'interval': interval}
    api = input("输入manager地址(http://" + config['manager_save']['url'] + ")：")
    if api:
        pass
    else:
        api = 'http://' + config['manager_save']['url']
    token = input("输入token：")
    worker_conf['manager'] = {"api_base": "\"" + api + "\"", "token": "\"" + token + "\""}
    cgroup = input("是否开启cgroup(Y/N)(N)")
    if cgroup == 'Y' or cgroup == 'y':
        base_path = input("输入base_path：")
        group = input("输入group：")
        worker_conf['cgroup'] = {'enable': 'true', 'base_path': "\"" + base_path + "\"", 'group': "\"" + group + "\""}
    else:
        base_path = ""
        group = ""
        worker_conf['cgroup'] = {'enable': 'false', 'base_path': "\"" + base_path + "\"", 'group': "\"" + group + "\""}
    hostname = input("输入主机名(localhost)：")
    if hostname:
        pass
    else:
        hostname = 'localhost'
    ip = '127.0.0.1'
    listen_addr = input("绑定IP(" + ip + ")：")
    if listen_addr:
        pass
    else:
        listen_addr = ip
    listen_port = input("绑定端口(6000)：")
    if listen_port:
        pass
    else:
        listen_port = '6000'
    worker_conf['server'] = {'hostname': "\"" + hostname + "\"", 'listen_addr': "\"" + listen_addr + "\"",
                             'listen_port': listen_port}
    ssl(1)
    worker_conf['include'] = {'include_mirrors ': "\"/etc/tunasync/mirrors/*.conf\""}
    worker_conf.write()
    config['manager_save']['worker'] = name
    config['manager_save']['path'] = worker_conf['global']['mirror_dir'][1:-1]
    with open('config.json', 'w') as cf:
        cf.write(json.dumps(config))
    cf.close()


def add_mirror():
    name = input("输入mirror名称(不能重复)：")
    mirror_conf.filename = '/etc/tunasync/mirrors/' + name + '.conf'
    provider = input("输入同步方式(rsync)：")
    if provider:
        pass
    else:
        provider = 'rsync'
    upstream = input("输入同步源(rsync方式的链接结尾必须为/)：")
    command = docker_image = size_pattern = ''
    if provider == "command":
        command = '\"' + input("输入同步脚本位置(绝对路径)：") + '\"'
        # docker_image = '\"' + input("设置docker镜像：") + '\"'
        # size_pattern = '\"' + input("设置大小格式(留空取消)：") + '\"'
    elif provider == "rsync":
        rsync_options = "[\"--info=progress2\", \"--no-inc-recursive\"]"
    else:
        pass
    interval = input("设置镜像同步周期(min)(留空沿用全局周期)：")
    c = input("是否启用ipv6?(Y/N)(N)")
    if c == 'Y' or c == 'y':
        use_ipv6 = 'true'
    else:
        use_ipv6 = 'false'
    memory_limit = input("内存限制(不填不限制)：")
    # exclude_file
    mirror = {"name": '\"' + name + '\"', "provider": '\"' + provider + '\"', "upstream": '\"' + upstream + '\"', "use_ipv6": use_ipv6}
    if command:
        mirror['command'] = command
        # mirror['docker_image'] = docker_image
        # if size_pattern:
        #     mirror['size_pattern'] = size_pattern
    if provider == "rsync":
        mirror['rsync_options'] = rsync_options
    if memory_limit:
        mirror['memory_limit'] = '\"' + memory_limit + '\"'
    if interval:
        mirror['interval'] = interval
    mirror_conf['[mirrors]'] = mirror
    config[name] = {'path': config['manager_save']['path'] + name, 'type': provider}
    mirror_conf.write()
    with open('config.json', 'w') as cf:
        cf.write(json.dumps(config))
    cf.close()
    print("重载Worker...")
    print(ctl_control('reload'))
    print("检测Worker状态...")
    status = systemd_control('status', 'worker')
    if status.find('failed') >= 0:
        print("Worker启动失败...\n", status)
        print("启动Worker...")
        systemd_control('start', 'worker')
    print("开始同步...")
    print(ctl_control('start', name))
    enable_auto('refresh', name)
    enable_auto('retry', name)


# 仅设置systemd，不设启动且不执行
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
### 基础设置部分结束


### systemd管理部分开始
def systemd_control(action, mode):
    if mode == 'manager':
        return delegator.run("systemctl " + action + " tunasync_manager").out
    elif mode == 'worker':
        return delegator.run("systemctl " + action + " tunasync_worker").out
### systemd管理部分结束


### 镜像管理开始
def ctl_control(action, mirror='', size=''):
    worker = config['manager_save']['worker']
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


def mirror_control(action, mirror):
    if action == 'del':
        print("删除文件...")
        print(delegator.run("rm -rf " + config[mirror]['path'] + ' /etc/tunasync/mirrors/' + mirror + '.conf').out)
        try:
            del_cron(mirror + '_size')
            del_cron(mirror + '_retry')
        except:
            pass
        print("操作tunasync...")
        print(ctl_control('reload'))
        print(ctl_control('disable', mirror))
        print(ctl_control('flush'))
        config.pop(mirror)
        with open('config.json', 'w') as df:
            df.write(json.dumps(config))
        df.close()
    elif action == 'disable':
        print("禁用中...")
        print(ctl_control('disable', mirror))
        try:
            del_cron(mirror + '_size')
            del_cron(mirror + '_retry')
        except:
            pass
        print(delegator.run("tunasynctl flush").out)
    elif action == 'enable':
        print("启用中...")
        print(ctl_control('start', mirror))
        try:
            enable_auto('retry', mirror)
            enable_auto('refresh', mirror)
        except:
            pass
        delegator.run("tunasynctl flush")
    elif action == 'refresh':
        get_size = "`du -sh " + config[mirror]['path'] + " | awk '{print $1}'`"
        print(ctl_control('set-size', mirror, get_size))
    elif action == 'logs':
        log = path + "/logs/" + mirror + '/latest'
        print(delegator.run("tail -n 10 " + log).out)


def get_info(mirror):
    jobs = requests.get("http://" + config['manager_save']['url'] + "/jobs").text
    list = json.loads(jobs)
    size = 'NULL'
    status = 'NULL'
    for job in list:
        if job['name'] == mirror:
            last_begin_time = job['last_started_ts']
            last_time = job['last_ended_ts']
            next_time = job['next_schedule_ts']
            pass_time = str(last_time - last_begin_time)
            if int(pass_time) <= 0:
                pass_time = '-'
            size = job['size']
            status = job['status']
            file_name = remain = speed = rate = total = chk_now = chk_remain = '-'
            if status == 'syncing' and config[mirror]['type'] == 'rsync':
                i = 0
                while i < 3:
                    logs = delegator.run('tail -3 ' + path + "/logs/" + mirror + '/latest').out.split("\n")
                    for log in logs:
                        if log.find('B/s') >= 0:
                            if log.find('xfr') >= 0:
                                chk = str(re.findall(r'[(](.*?)[)]', log)[0])
                                chk_now = re.findall(r'[#](.*?)[,]', chk)[0]
                                chk_remain = re.findall(r'[=](.*?)[/]', chk)[0]
                                total = chk.split("/")[1]
                            infos = log.split(" ")
                            for info in infos:
                                if info.find('%') >= 0:
                                    rate = info
                                elif info.find('B/s') >= 0:
                                    speed = info
                                elif info.find(':') >= 0:
                                    remain = info
                                elif info.find('=') >= 0 or info.find('#') >= 0:
                                    pass
                                elif info:
                                    size = info
                        elif log:
                            files = log.split('/')
                            file_name = files[-1]
                    try:
                        return {'status': status, 'size': size, 'last_time': last_time, 'pass_time': pass_time, 'chk_now': chk_now, 'chk_remain': chk_remain, 'total': total, 'rate': rate, 'speed': speed, 'remain': remain, 'file_name': file_name, 'next_time': next_time}
                    except:
                        i += 1
            return {'status': status, 'size': size, 'last_time': last_time, 'pass_time': pass_time, 'next_time': next_time}


def enable_auto(mode, mirror):
    if mode == 'refresh':
        time_m = input("设置自动更新大小的时间间隔，例如(30min)或(6h)，留空取消：")
        if time_m:
            if time_m.find('min') >= 0 :
                time = "*/" + time_m[:-3] + " * * * *"
            elif time_m.find('h') >= 0:
                time = "* */" + time_m[:-1] + " * * *"
            else:
                print("时间格式错误！")
                return 0
        else:
            print("不设置大小检测")
            return 0
        command = "/usr/bin/python3 " + path + "/refresh.py " + config['manager_save']['worker'] + " " + mirror + " " + config[mirror]['type'] + " " + path + "/logs/" + mirror + " " + config[mirror]['path']
        add_cron(command, time, mirror + '_size')
    elif mode == 'retry':
        time_m = input("设置自动检测同步错误并重试的时间间隔，例如(30min)或(6h)，留空取消：")
        if time_m:
            if time_m.find('min') >= 0:
                time = "*/" + time_m[:-3] + " * * * *"
            elif time_m.find('h') >= 0:
                time = "* */" + time_m[:-1] + " * * *"
            else:
                print("时间格式错误！")
                return 0
        else:
            print("不设置自动重试")
            return 0
        command = "/usr/bin/python3 " + path + "/retry.py " + config['manager_save']['worker'] + " " + mirror
        add_cron(command, time, mirror + '_retry')
### 镜像管理结束

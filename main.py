import time
import delegator
from prettytable import PrettyTable
from utils import ins_bin, init_manager, init_worker, systemd, get_config, systemd_control, ctl_control, mirror as dx


def init():
    print("检测tunasync是否存在...")
    code = 1
    cmd = delegator.run("/usr/bin/tunasync -v")
    print(cmd.out)
    if cmd.return_code != 0:
        code = 0
    cmd = delegator.run("/usr/bin/tunasynctl -v")
    print(cmd.out)
    if cmd.return_code != 0:
        code = 0
    if code == 1:
        print("tunasync已存在，无需安装...")
    else:
        print("开始安装...")
        if ins_bin() < 0:
            print("安装tunasync时出错\n您可以自行将tunasync和tunasynctl放置到/usr/bin目录后再进行初始化操作...")
            return 0
        else:
            pass
    try:
        print("开始设置manager...")
        init_manager()
        print("开始设置服务...")
        systemd()
        print("启动manager...")
        systemd_control('start', 'manager')
        print("设置manager自启...")
        systemd_control('enable', 'manager')
        print("开始设置worker...")
        init_worker()
        # print("启动worker...")
        # systemd_control('start', 'worker')
        # print("设置worker自启...")
        # systemd_control('enable', 'worker')
        print("worker将不会启动直到新增第一个mirror...")
    except:
        print("设置时出错...")


def control():
    config = get_config()
    table = PrettyTable(['序号', '名称', '状态', '大小', '上次同步时间(用时s)', '下次同步时间', '当前进度', '当前速度', '剩余时间', '剩余文件/总数', '当前文件(序号)'])
    table.align = 'l'
    for i, name in enumerate(config):
        if name == 'manager_save':
            pass
        else:
            info = dx(name).info()
            try:
                last_time = time.strftime("%m-%d %H:%M:%S", time.localtime(int(info['last_time'])))
                next_time = time.strftime("%m-%d %H:%M:%S", time.localtime(int(info['next_time'])))
                if last_time == next_time:
                    last_time = '正在首次同步'
                    next_time = '-'
                if info['status'] == 'syncing' and config[name]['type'] == 'rsync':
                    try:
                        table.add_row([i, name, info['status'], info['size'], '{}({})'.format(last_time, info['pass_time']), next_time, info['rate'], info['speed'], info['remain'], '{}/{}'.format(info['chk_remain'], info['total']), '{}({})'.format(info['file_name'], info['chk_now'])])
                        ctl_control('set-size', name, info['size'])
                    except:
                        table.add_row([i, name, info['status'], info['size'], '{}({})'.format(last_time, info['pass_time']), next_time, '获', '取', '失', '败', '...'])
                else:
                    table.add_row([i, name, info['status'], info['size'], '{}({})'.format(last_time, info['pass_time']), next_time, '-', '-', '-', '-', '-'])
            except:
                try:
                    table.add_row([i, name, 'disabled', '', '', '', '', '', '', '', ''])
                except:
                    pass
    print(table)
    id = input("输入需要操作的镜像序号(留空返回)：")
    if id:
        id = int(id)
    else:
        return 0
    i = 0
    name = ''
    for mirror in config:
        if i == id:
            name = mirror
        i += 1
    if name == '':
        print("序号不存在")
        return 0
    else:
        mirror = dx(name)
    mode = input("请选择操作：\n1.删除镜像\n2.禁用镜像\n3.启用镜像\n4.停止同步\n5.开始同步\n6.立即更新大小\n7.立即重试\n8.查看日志最后10行\n9.返回\n")
    if mode:
        mode = int(mode)
    else:
        return 0
    if mode == 1:
        mirror.delete()
    elif mode == 2:
        mirror.disable()
    elif mode == 3:
        mirror.enable()
    elif mode == 4:
        ctl_control('stop', name)
    elif mode == 5:
        ctl_control('start', name)
    elif mode == 6:
        mirror.refresh()
    elif mode == 7:
        ctl_control('restart', name)
    elif mode == 8:
        mirror.logs()
    else:
        pass
    del mirror


def systemctl():
    mode = input(
        "请选择操作：\n1.查看Manager状态\n2.启动Manager\n3.关闭Manager\n4.重启Manager\n5.启用Manager自启\n6.禁用Manager自启\n\n7.查看Worker状态\n8.启动Worker\n9.关闭Worker\n10.重启Worker\n11.启用Worker自启\n12.禁用Worker自启\n")
    if mode:
        mode = int(mode)
    else:
        return 0
    if mode == 1:
        print(systemd_control('status', 'manager'))
    elif mode == 2:
        print(systemd_control('start', 'manager'))
    elif mode == 3:
        print(systemd_control('stop', 'manager'))
    elif mode == 4:
        print(systemd_control('restart', 'manager'))
    elif mode == 5:
        print(systemd_control('enable', 'manager'))
    elif mode == 6:
        print(systemd_control('disable', 'manager'))
    elif mode == 7:
        print(systemd_control('status', 'worker'))
    elif mode == 8:
        print(systemd_control('start', 'worker'))
    elif mode == 9:
        print(systemd_control('stop', 'worker'))
    elif mode == 10:
        print(systemd_control('restart', 'worker'))
    elif mode == 11:
        print(systemd_control('enable', 'worker'))
    elif mode == 12:
        print(systemd_control('disable', 'worker'))


def menu():
    try:
        while 1:
            mode = input("欢迎使用tunasync管理系统，请选择功能：(首次需进行初始化)\n1.初始化\n2.新增镜像\n3.镜像管理\n4.进程管理\n5.退出\n")
            if mode:
                mode = int(mode)
            else:
                break
            if mode == 1:
                init()
            elif mode == 2:
                name = input("输入mirror名称(不能重复)：")
                dx(name).add()
            elif mode == 3:
                control()
            elif mode == 4:
                systemctl()
            else:
                return 0
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    menu()

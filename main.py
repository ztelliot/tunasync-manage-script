import time
import delegator
from utils import bin, build, init_manager, init_worker, add_mirror, systemd, config, get_info, systemd_control, ctl_control, mirror_control


def init(mode):
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
        if mode:
            mode = int(mode)
        else:
            mode = 2
        print("开始安装...")
        try:
            if mode == 1:
                if bin() < 0:
                    print("安装tunasync时出错\n您可以自行将tunasync和tunasynctl放置到/usr/bin目录后再进行初始化操作...")
                    return 0
                else:
                    pass
            else:
                if build() < 0:
                    print("安装tunasync时出错\n您可以自行将tunasync和tunasynctl放置到/usr/bin目录后再进行初始化操作...")
                    return 0
                else:
                    pass
        except:
            print("安装tunasync时出错\n您可以自行将tunasync和tunasynctl放置到/usr/bin目录后再进行初始化操作...")
            return 0
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
        print("启动worker...")
        systemd_control('start', 'worker')
        print("设置worker自启...")
        systemd_control('enable', 'worker')
    except:
        print("设置时出错...")


def mirror():
    print("序号\t名称\t\t状态\t\t大小\t\t上次同步时间(用时s)\t\t下次同步时间\t\t当前进度\t当前速度\t剩余时间\t剩余文件/总数\t当前文件(序号)")
    i = 0
    for mirror in config:
        if mirror == 'manager_save':
            pass
        else:
            info = get_info(mirror)
            try:
                last_time = time.strftime("%m-%d %H:%M:%S", time.localtime(int(info['last_time'])))
                next_time = time.strftime("%m-%d %H:%M:%S", time.localtime(int(info['next_time'])))
                if last_time == next_time:
                    last_time = '正在首次同步'
                    next_time = '-\t'
                if info['status'] == 'syncing' and config[mirror]['type'] == 'rsync':
                    try:
                        print(str(i) + '\t' + mirror + '\t\t' + info['status'] + '\t\t' + info['size'] + '\t\t' + last_time + '(' + info['pass_time'] + ')\t\t' + next_time + '\t\t' + info['rate'] + '\t\t' + info['speed'] + '\t' + info['remain'] + '\t\t' + info['chk_remain'] + '/' + info['total'] + '\t' + info['file_name'] + '(' + info['chk_now'] + ')')
                        ctl_control('set-size', mirror, info['size'])
                    except:
                        print(str(i) + '\t' + mirror + '\t\t' + info['status'] + '\t\t' + info['size'] + '\t\t' + last_time + '(' + info['pass_time'] + ')\t\t' + next_time + '\t\t获取失败，请重试')
                else:
                    print(str(i) + '\t' + mirror + '\t\t' + info['status'] + '\t\t' + info['size'] + '\t\t' + last_time + '(' + info['pass_time'] + ')\t\t' + next_time + '\t\t-\t\t-\t\t-\t\t-\t\t-')
            except:
                try:
                    print(str(i) + '\t' + mirror + '\t\tdisabled')
                except:
                    pass
        i += 1
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
    mode = input("请选择操作：\n1.删除镜像\n2.禁用镜像\n3.启用镜像\n4.停止同步\n5.开始同步\n6.立即更新大小\n7.立即重试\n8.查看日志最后10行\n9.返回\n")
    if mode:
        mode = int(mode)
    else:
        return 0
    if mode == 1:
        mirror_control('del', name)
    elif mode == 2:
        mirror_control('disable', name)
    elif mode == 3:
        mirror_control('enable', name)
    elif mode == 4:
        ctl_control('stop', name)
    elif mode == 5:
        ctl_control('start', name)
    elif mode == 6:
        mirror_control('refresh', name)
    elif mode == 7:
        ctl_control('restart', name)
    elif mode == 8:
        mirror_control('logs', name)
    else:
        pass


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
                mode = input("1.通过预编译文件方式(仅支持x86_64架构)\n2.通过编译方式\n(默认通过编译安装)\n")
                init(mode)
            elif mode == 2:
                add_mirror()
            elif mode == 3:
                mirror()
            elif mode == 4:
                systemctl()
            else:
                return 0
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    menu()

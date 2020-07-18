# tunasync简易管理器
A Python tool to help manage tunasync in an easier way

## 简介
    本管理器能实现简单的tunasync管理，包括安装、manager/worker设置、mirror管理

## 如何使用 / HowTo
    安装Python3、pip、rsync
    yum install -y python3 python3-pip rsync
    或
    apt install -y python3 python3-pip rsync
    确认系统使用systemd进行进程管理
    ps -p 1 -o comm=
    确定crond状态
    systemctl status crond
    如为关闭状态，则需将其打开
    systemctl enable crond
    systemctl start crond
    安装依赖
    pip3 install -r requirements.txt
    随后可以通过 python3 main.py 启动脚本
    脚本首次使用需要进行初始化，程序将会自动安装tunasync在/usr/bin目录下，然后请根据向导进行设置
    
   ### 关于tunasync的安装
   #### 预编译文件方式
    由于官方仅提供x86_64的二进制编译文件，故该方法仅支持x86_64架构的处理器
   ### 编译方式
    因为需要安装golang、git、make，而安装默认使用包管理器
    因此本自动化编译仅在CentOS7+/Ubuntu18.04+和x86_64/i386/aarch64环境上能较好的完成
    其他系统/架构未经测试，可能需要手动编译

## 已知问题
    对于使用command方式同步的镜像暂时无法获取进度，且同步过程中有较大概率出现错误

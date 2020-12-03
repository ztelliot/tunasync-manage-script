# tunasync简易管理器
A Python tool to help manage tunasync in an easier way

## 简介
   本管理器能实现简单的tunasync管理，包括安装、manager/worker设置、mirror管理

## 如何使用 / HowTo
   安装Python3、pip、rsync
   
   `yum install -y python3 python3-pip rsync`
   或
   `apt install -y python3 python3-pip rsync`
   
   确认系统使用systemd进行进程管理
   
   `ps -p 1 -o comm=`
   
   克隆本项目
   
   `git clone https://github.com/ztelliot/tunasync-manage-script.git && cd tunasync-manage-script`

   安装依赖
   
   `pip3 install -r requirements.txt`
   
   随后可以通过 `python3 main.py` 启动脚本
   
   脚本首次使用需要进行初始化，程序将会自动安装tunasync在`/usr/bin`目录下，然后请根据向导进行设置
    
   ### 关于tunasync的安装
   官方提供x86_64和arm64的二进制编译文件，故仅支持x86_64和arm64架构处理器

## 已知问题
    对于使用command方式同步的镜像暂时无法获取进度，且同步过程中有较大概率出现错误

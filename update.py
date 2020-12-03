import json
import delegator
from utils import get_config, path, size_format


config = get_config()
list = json.loads(delegator.run("tunasynctl list --all").out.strip('\n'))
worker = config['manager_save']['worker']
for info in list:
    mirror = info['name']
    type = config[mirror]['type']
    mirror_path = config[mirror]['path']
    if type == 'rsync' and info['status'] == 'success':
        get_size = "`tac " + config['manager_save']['log_path'] + mirror + "/latest | grep \"^Total file size: \" | head -n 1 | grep -Po \"[0-9\\.]+[MGT]\"`"
    else:
        try:
            get_size = size_format(int(delegator.run("du -s " + mirror_path + " | awk '{print $1}'").out))
        except:
            get_size = "`du -sh " + mirror_path + " | awk '{print $1}'`"
    command = "tunasynctl set-size -w " + worker + " " + mirror + " " + get_size
    print(delegator.run(command).out)
    if info['status'] == 'failed':
        print(mirror + "执行失败，开始重试...")
        print(delegator.run("tunasynctl restart -w " + worker + " " + mirror).out)

import json
import delegator
import sys


worker = sys.argv[1]
mirror = sys.argv[2]
type = sys.argv[3]
log_path = sys.argv[4]
mirror_path = sys.argv[5]
list = json.loads(delegator.run("tunasynctl list --all").out)
get_size = ''
for info in list:
    if info['name'] == mirror:
        if type == 'rsync' and info['status'] == 'success':
            get_size = "`tac " + log_path + "/latest | grep \"^Total file size: \" | head -n 1 | grep -Po \"[0-9\\.]+[MGT]\"`"
        else:
            get_size = "`du -sh " + mirror_path + " | awk '{print $1}'`"
command = "tunasynctl set-size -w " + worker + " " + mirror + " " + get_size
print(delegator.run(command).out)
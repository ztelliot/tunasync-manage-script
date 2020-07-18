import json
import delegator
import sys


worker = sys.argv[1]
mirror = sys.argv[2]
list = json.loads(delegator.run("tunasynctl list --all").out)
for info in list:
    if info['name'] == mirror and info['status'] == 'failed':
        print(mirror + "执行失败，开始重试...")
        print(delegator.run("tunasynctl restart -w " + worker + " " + mirror).out)

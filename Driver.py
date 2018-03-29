from AutoScaler import *
import time

_ami = 'ami-f4756494' # ami for app-tier-auto
_req_queue_url = 'https://sqs.us-west-1.amazonaws.com/791943463301/image-request'
_sleep_time = 2.0

scaler = AutoScaler(ami=_ami, \
                    req_queue_url=_req_queue_url)

while True:
    scaler.run()
    time.sleep(_sleep_time)

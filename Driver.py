from AutoScaler import *
import time

_ami = 'ami-ce3422ae' # ami for backend-server-1
_req_queue_url = 'https://sqs.us-west-1.amazonaws.com/791943463301/imagerecognition-request'
_sleep_time = 0.1

scaler = AutoScaler(ami=_ami, \
                    req_queue_url=_req_queue_url)
scaler.setup()

while True:
    scaler.run()
    time.sleep(_sleep_time)

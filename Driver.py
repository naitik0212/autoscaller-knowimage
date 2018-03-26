from AutoScaler import *
import time

_ami = 'ami-9eddcbfe' # ami for backend-server-2
_req_queue_url = 'https://sqs.us-west-1.amazonaws.com/791943463301/imagerecognition-request'
_sleep_time = 1.0

scaler = AutoScaler(ami=_ami, \
                    req_queue_url=_req_queue_url)
scaler.setup()

while True:
    scaler.run()
    time.sleep(_sleep_time)

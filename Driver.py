from AutoScaler import *
import time

_ami = 'ami-1eb7a17e' # ami for backend-server
_req_queue_url = 'https://sqs.us-west-1.amazonaws.com/791943463301/imagerecognition-request'
_sleep_time = 2.0

scaler = AutoScaler(ami=_ami, \
                    req_queue_url=_req_queue_url)
scaler.setup()

while True:
    scaler.run()
    time.sleep(_sleep_time)

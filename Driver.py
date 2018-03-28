from AutoScaler import *
import time

_ami = 'ami-a8a5b3c8' # ami for backend-server
_req_queue_url = 'https://sqs.us-west-1.amazonaws.com/050256975407/imagerecognition-request'
_sleep_time = 2.0

scaler = AutoScaler(ami=_ami, \
                    req_queue_url=_req_queue_url)
scaler.setup()

while True:
    scaler.run()
    time.sleep(_sleep_time)

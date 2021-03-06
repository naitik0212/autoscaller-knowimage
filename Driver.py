from AutoScaler import *
import time

_ami = '****' # ami for app-tier-auto Naitik's
_req_queue_url = 'https://sqs.us-west-1.amazonaws.com/***/image-request'
_sleep_time = 2.0

scaler = AutoScaler(ami=_ami, \
                    req_queue_url=_req_queue_url)

while True:
    scaler.run()
    time.sleep(_sleep_time)

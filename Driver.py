from AutoScaler import *
import time

scaler = AutoScaler(ami='ami-ff188587', \
                    req_queue_url='https://sqs.us-west-2.amazonaws.com/791943463301/myQueue2')

while True:
    scaler.run()
    time.sleep(0.1)

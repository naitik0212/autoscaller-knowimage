import time
from SQSMonitor import *

url = 'https://sqs.us-west-1.amazonaws.com/791943463301/imagerecognition-request'
sqs_obj = SQSMonitor(url)

while(True):
    sqs_obj.num_messages()
    time.sleep(2.0)

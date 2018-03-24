from AutoScaler import *
import time

_ami = 'ami-840016e4'
_req_queue_url = 'https://sqs.us-west-1.amazonaws.com/791943463301/imagerecognition-request'
_sleep_time = 0.1

scaler = AutoScaler(ami=_ami, \
                    req_queue_url=_req_queue_url)
scaler.setup()

while True:
    scaler.run()
    time.sleep(_sleep_time)

# from EC2instanceController import *
# import time
#
# ec2ic = EC2InstanceController('ami-ff188587')
#
# ec2ic.run_instances(1)
#
# t = time.time()
#
# print 'starting instances...'
# for i in ec2ic.starting_list:
#     ins = ec2ic.starting_list[i]
#     print ins.iid, ins.privateIP, ins.publicIP, ins.state
#
# print ''
#
# starting = True
# while(starting):
#     for i in ec2ic.starting_list:
#         ins = ec2ic.starting_list[i]
#         # response = boto3.client('ec2').describe_instance_status(InstanceIds=[ins.iid])
#         # print response
#         state = boto3.resource('ec2').Instance(ins.iid).state['Name']
#         print state
#         if state == "running":
#             starting = False
#
# print 'started in sec: ', (time.time() - t)
#
# print ''
# print "terminating..."
# for i in ec2ic.starting_list:
#     iidlist = [ec2ic.starting_list[i].iid]
#     ec2ic.terminate(iidlist)

from EC2instanceController import *
from SQSMonitor import *
import math


class AutoScaler(object):
    def __init__(self, ami, req_queue_url):
        # static assignments
        self.ami = ami
        self.req_queue_url = req_queue_url

        # thresholds and parameters
        self.max_instances_allowed = 18

        # monitoring parameters
        self.num_pending_requests = 0
        self.num_instances_busy = 0
        self.num_instances_starting = 0

        # analyse and compute parameters
        self.num_instances_to_start = 0

        # components
        self.ec2ic = EC2InstanceController(self.ami, self.max_instances_allowed)
        self.sqsm = SQSMonitor(self.req_queue_url)

    def run(self):
        # a single run of the auto-scaler algorithm
        self.monitor()
        self.analyse()
        self.execute()

    def monitor(self):
        # update all the 'monitoring parameters' of the system

        # read the number of pending requests
        self.num_pending_requests = self.sqsm.num_messages()

        # read the number of instances starting
        self.num_instances_starting = self.ec2ic.get_numStarting()

        # read the number of busy instances
        self.num_instances_busy = self.ec2ic.get_numRunning()

        print "num running: " + str(self.num_instances_busy)
        print "num starting: " + str(self.num_instances_starting)

    def analyse(self):
        # check the number of busy/idling instances
        num_ready = self.num_instances_busy + self.num_instances_starting

        self.num_instances_to_start = max(0, self.num_pending_requests - num_ready)

        # validate with respect to threshold
        max_new_starts_allowed = self.max_instances_allowed - (num_ready)
        self.num_instances_to_start = min(self.num_instances_to_start, max_new_starts_allowed)

    def execute(self):
        # start instances
        if self.num_instances_to_start > 0:
            self.ec2ic.run_instances(self.num_instances_to_start)
            self.num_instances_to_start = 0

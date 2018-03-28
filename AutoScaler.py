from EC2instanceController import *
from SQSMonitor import *
import math


class AutoScaler(object):
    def __init__(self, ami, req_queue_url):
        # static assignments
        self.ami = ami
        self.req_queue_url = req_queue_url

        # thresholds and parameters
        self.min_instances_allowed = 1
        self.max_instances_allowed = 18
        self.max_pending_requests_allowed = 0
        self.timeout_idle_total = 0
        self.timeout_idle_since = 0
        self.time_per_req = 4.5
        self.start_time_total = 40.0
        self.prediction_factor = 2

        # monitoring parameters
        self.num_pending_requests = 0
        self.num_instances_busy = 0
        self.num_instances_idle_now = 0
        self.num_instances_starting = 0

        # analyse and compute parameters
        self.num_instances_to_start = 0
        self.stop_iids = []

        # components
        self.ec2ic = EC2InstanceController(self.ami, 19)
        self.sqsm = SQSMonitor(self.req_queue_url)


    def setup(self):
        # check running instances

        # initial setup of the ec2 cluster
        self.stop_iids = []
        self.num_instances_to_start = self.min_instances_allowed
        self.execute()

    def run(self):
        # a single run of the auto-scaler algorithm
        self.monitor()
        self.analyse()
        self.execute()

    def monitor(self):
        # update all the 'monitoring parameters' of the system

        # read the number of pending requests
        self.num_pending_requests = self.sqsm.num_messages()

        # update instance states
        self.ec2ic.update_instance_states()

        # read the number of instances starting
        self.num_instances_starting = len(self.ec2ic.starting_list)

        # read the number of busy instances
        self.num_instances_busy = len(self.ec2ic.busy_list)

        # read the number of idle instances
        self.num_instances_idle_now = len(self.ec2ic.idle_list)

    def analyse(self):
        # check the number of busy/idling instances
        num_ready = self.num_instances_busy + self.num_instances_idle_now

        self.num_instances_to_start = max(0, self.num_pending_requests - num_ready - self.num_instances_starting)

        # validate with respect to threshold
        max_new_starts_allowed = self.max_instances_allowed - (num_ready + self.num_instances_starting)
        self.num_instances_to_start = min(self.num_instances_to_start, max_new_starts_allowed)

        # prepare a list of instances to be stopped
        if num_ready > 0:
            timeout_idle = int(math.ceil(self.timeout_idle_total / num_ready))
            idle_list = self.ec2ic.idle_list
            for iid in idle_list:
                if idle_list[iid].idle_since >= self.timeout_idle_since:
                    if idle_list[iid].idle_total >= timeout_idle:
                        if (num_ready-len(self.stop_iids)) \
                                <= self.min_instances_allowed:
                            break
                        self.stop_iids.append(iid)


    def execute(self):
        # stop instances
        if len(self.stop_iids) > 0:
            print 'stopping ' + str(len(self.stop_iids)) + ' instances: ',
            for iid in self.stop_iids:
                print iid,
            print ''
            self.ec2ic.terminate(self.stop_iids)
            self.stop_iids = []

        # start instances
        if self.num_instances_to_start > 0:
            self.ec2ic.run_instances(self.num_instances_to_start)
            self.num_instances_to_start = 0


class AutoScaler2(AutoScaler):
    def __init__(self, ami, req_queue_url):
        AutoScaler.__init__(self,ami, req_queue_url)
        self.ec2ic = EC2InstanceController2(self.ami, self.max_instances_allowed)

    def analyse(self):
        # check the number of busy/idling instances
        num_ready = self.num_instances_busy

        self.num_instances_to_start = self.num_pending_requests - num_ready - self.num_instances_starting

        if self.num_instances_to_start > 0:
            # validate with respect to threshold
            max_new_starts_allowed = self.max_instances_allowed - (num_ready + self.num_instances_starting)
            self.num_instances_to_start = min(self.num_instances_to_start, max_new_starts_allowed)
        elif self.num_instances_to_start < 0:
            if len(self.ec2ic.busy_list)>0:
                for iid in self.ec2ic.busy_list:
                    if (num_ready-len(self.stop_iids)) > self.min_instances_allowed:
                        self.stop_iids.append(iid)
                    else:
                        break
                    self.num_instances_to_start += 1
                    if self.num_instances_to_start == 0:
                        break
            self.num_instances_to_start = 0

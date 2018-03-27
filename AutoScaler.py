from EC2instanceController import *
from SQSMonitor import *
import math


class AutoScaler(object):
    def __init__(self, ami, req_queue_url):
        # static assignments
        self.ami = ami
        self.req_queue_url = req_queue_url

        # components
        self.ec2ic = EC2InstanceController(self.ami)
        self.sqsm = SQSMonitor(self.req_queue_url)

        # thresholds and parameters
        self.min_instances_allowed = 1
        self.max_instances_allowed = 18
        self.max_pending_requests_allowed = 0
        self.timeout_idle_total = 40
        self.timeout_idle_since = 5
        self.time_per_req = 5.0
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

    def setup(self):
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
        num_ready = self.num_instances_busy + self.num_instances_idle_now + 1

        # predict the number of requests that can be served in next 40 sec
        predicted = num_ready * (math.ceil(self.start_time_total / self.time_per_req))

        # check the number of starting instances and for each one, give their prediction
        for iid in self.ec2ic.starting_list:
            ins = self.ec2ic.starting_list[iid]
            predicted += int(math.ceil(ins.starting_since / self.time_per_req))

        # number of requests remaining to be handled in 40 sec is...
        num_req_later = self.num_pending_requests - predicted

        # calculate number of instances to start
        if num_req_later > 0:
            self.num_instances_to_start = num_req_later
        else:
            if predicted > (self.prediction_factor * self.num_pending_requests):
                self.num_instances_to_start = 1
            else:
                self.num_instances_to_start = 0

        # validate with respect to threshold
        max_new_starts_allowed = self.max_instances_allowed \
                                 - (num_ready + self.num_instances_starting)
        self.num_instances_to_start = min(self.num_instances_to_start, max_new_starts_allowed)

        # prepare a list of instances to be stopped
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
            print 'starting ' + str(self.num_instances_to_start) + ' instances...'
            print ''
            self.ec2ic.run_instances(self.num_instances_to_start)
            self.num_instances_to_start = 0




























        # # use monitoring parameters to compute instances to start/stop
        #
        # # calculate maximum number of new instances allowed to start
        # active_instances = self.num_instances_busy + self.num_instances_starting + self.num_instances_idle_now
        # max_new_instances_allowed = self.max_instances_allowed - active_instances
        #
        # # compute number of instances required to meet the demand
        # if self.num_pending_requests > self.max_pending_requests_allowed:
        #     start_count = self.num_pending_requests - self.num_instances_starting
        # else:
        #     start_count = 0
        #
        # # compute actual start count based on thresholds
        # if start_count < 0:
        #     actual_start_count = 0
        # elif start_count > max_new_instances_allowed:
        #     actual_start_count = max_new_instances_allowed
        # else:
        #     actual_start_count = start_count
        #
        # self.num_instances_to_start = actual_start_count
        #

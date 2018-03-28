import boto3
from botocore.exceptions import ClientError
import time
import requests
import math


class EC2InstanceController(object):
    # A client to manage Amazon EC2 instances

    def __init__(self, ami, max_instances):
        # AWS EC2 SDK client
        self.ec2 = boto3.client('ec2')

        # AWS image id
        self.image_id = ami

        self.max_allowed = max_instances

        # instance type
        self.instance_type = 't2.micro'

        # key name
        self.key_name = 'Cloud_Project'

        # security groups
        # sg_default = 'sg-389dd947'
        sg546 = 'sg-7f93b606'
        self.security_group_ids = [sg546]

        # list of active instances
        self.starting_list = {}
        self.busy_list = {}
        self.idle_list = {}

    def run_instances(self, count):
        # validate max allowed instances
        try:
            response = boto3.client('ec2').describe_instances()
        except:
            print ""
        run_count = 0
        for res in response['Reservations']:
            for desc in res['Instances']:
                if (desc['State']['Name'] == 'running') or (desc['State']['Name'] == 'pending') or (desc['State']['Name'] == 'shutting-down'):
                    run_count += 1

        if (count + run_count) > self.max_allowed:
            count = self.max_allowed - run_count
            if count <= 0: return

        print 'starting ' + str(count) + ' instances...'
        print ''

        # define network iterface
        net_int = {'AssociatePublicIpAddress' : True}
        net_ints = [net_int]

        # do a dry run first to check permissions
        try:
            response = self.ec2.run_instances(ImageId=self.image_id, \
                                              InstanceType=self.instance_type, \
                                              KeyName=self.key_name, \
                                              MinCount=1, \
                                              MaxCount=1, \
                                              Monitoring={'Enabled': False}, \
                                              SecurityGroupIds=self.security_group_ids, \
                                              DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # dry run succeeded. Launch instances
        try:
            tag = {'Key': 'Name', 'Value': 'app-tier-auto'}
            TagSpecification = {'ResourceType':'instance', 'Tags':[tag]}
            response = self.ec2.run_instances(ImageId=self.image_id, \
                                              InstanceType=self.instance_type, \
                                              KeyName=self.key_name, \
                                              MinCount=int(count), \
                                              MaxCount=int(count), \
                                              TagSpecifications=[TagSpecification], \
                                              Monitoring={'Enabled': False}, \
                                              SecurityGroupIds=self.security_group_ids, \
                                              DryRun=False)

            for i in response['Instances']:
                # define EC2Instance object
                instance_id = i['InstanceId']
                new_instance = EC2Instance(iid=instance_id, \
                                           privateIP=i['PrivateIpAddress'], \
                                           publicIP=boto3.resource('ec2').Instance(instance_id).public_ip_address, \
                                           state='starting')
                # add to starting list
                self.starting_list[instance_id] = new_instance

            return response

        except ClientError as e:
            print(e)

    def terminate(self, instance_ids):
        # stop instances of given instance ids
        response = self.ec2.terminate_instances(InstanceIds=instance_ids)

        # remove stopped instances from idle list
        for instance_id in instance_ids:
            del self.idle_list[instance_id]

    def update_instance_states(self):
        # check and update state of each instance
        starting_to_idle = []
        starting_to_busy = []
        busy_to_idle = []
        idle_to_busy = []

        for iid in self.starting_list:
            state = self.starting_list[iid].update_state()
            if state=='busy':
                starting_to_busy.append(self.starting_list[iid])
            if state=='idle':
                starting_to_idle.append(self.starting_list[iid])

        for iid in self.busy_list:
            state = self.busy_list[iid].update_state()
            if state=='idle':
                busy_to_idle.append(self.busy_list[iid])

        for iid in self.idle_list:
            state = self.idle_list[iid].update_state()
            if state=='busy':
                idle_to_busy.append(self.idle_list[iid])

        for i in starting_to_idle:
            self.idle_list[i.iid] = i
            del self.starting_list[i.iid]

        for i in starting_to_busy:
            self.busy_list[i.iid] = i
            del self.starting_list[i.iid]

        for i in busy_to_idle:
            self.idle_list[i.iid] = i
            del self.busy_list[i.iid]

        for i in idle_to_busy:
            self.busy_list[i.iid] = i
            del self.idle_list[i.iid]


class EC2Instance(object):
    # local object representation of ec2 instance

    def __init__(self, iid, privateIP, publicIP, state):
        self.iid = iid
        self.privateIP = str(privateIP)
        self.publicIP = str(publicIP)
        self.state = state
        self.start_delay = 15

        self.idle_since = 0
        self.idle_total = 0
        self.busy_since = 0
        self.starting_since = 0
        self.started_since = 0
        self.avg_busy_time = 5.0

        self.prev_time = time.time()
        self.ec2 = boto3.client('ec2')

    def update_state(self):
        # generate seconds pulse
        curr_time = time.time()
        sec_pulse = math.floor(curr_time-self.prev_time)
        self.prev_time = curr_time

        # new state must be one of these: starting, idle, busy

        if self.state == 'starting':
            state = boto3.resource('ec2').Instance(self.iid).state['Name']
            if state != 'running':
                self.busy_since = 0
                self.idle_since = 0
                self.starting_since += sec_pulse
                return
            else:
                print "waiting for spring boot on " + self.iid + "..."
                self.starting_since += sec_pulse
                self.started_since += sec_pulse
                if self.started_since < self.start_delay:
                    self.busy_since = 0
                    self.idle_since = 0
                    return

        state = self.check_busy()
        prev_state = self.state

        if state == 'busy':
            self.state = state
            self.idle_since = 0
            self.starting_since = 0
            self.busy_since += sec_pulse
        elif state == 'idle':
            self.starting_since = 0
            self.busy_since = 0
            self.idle_since += sec_pulse
            self.idle_total += sec_pulse
            self.state = state

        return self.state

    def check_busy(self):

        try:
            if str(self.publicIP) == "":
                self.publicIP = str(boto3.resource('ec2').Instance(self.iid).public_ip_address)
            req_url = "http://" + str(self.publicIP) + ":8080/cloudimagerecognition"
            r = requests.get(req_url)
        except:
            if self.publicIP == "":
                print "check busy error: no public ip"
            print "check busy connection error"
            return 'busy'

        if str(r.text) == 'true':
            status = 'busy'
        else:
            status = 'idle'
        return status

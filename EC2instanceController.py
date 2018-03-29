import boto3
from botocore.exceptions import ClientError


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
        self.key_name = 'aws-ec2'

        # security groups
        # sg_default = 'sg-389dd947'
        sg546 = 'sg-53097a2a'
        self.security_group_ids = [sg546]

        # list of instances started
        self.instances = []

    def run_instances(self, start_count):
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

        run_count -= 2  # disregard the web tier and stand-alone app tier

        if (start_count + run_count) > self.max_allowed:
            start_count = self.max_allowed - run_count
            if start_count <= 0: return

        print 'starting ' + str(start_count) + ' instances...'
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
                                              MinCount=int(start_count), \
                                              MaxCount=int(start_count), \
                                              TagSpecifications=[TagSpecification], \
                                              Monitoring={'Enabled': False}, \
                                              SecurityGroupIds=self.security_group_ids, \
                                              DryRun=False)

            # create a list of instances started
            for instance in response['Instances']:
                self.instances.append(str(instance['InstanceId']))

        except ClientError as e:
            print(e)

    def terminate_all(self):
        terminate_list = []
        for iid in self.instances:
            state = boto3.resource('ec2').Instance(iid).state['Name']
            if (state == 'running') or (state == 'pending'):
                terminate_list.append(iid)
        if terminate_list:
            self.terminate(terminate_list)
        self.instances = []

    def terminate(self, instance_ids):
        # stop instances of given instance ids
        response = self.ec2.terminate_instances(InstanceIds=instance_ids)

    def get_numStarting(self):
        return self.get_state_count('pending')

    def get_numRunning(self):
        return max(0,(self.get_state_count('running') - 2))

    def get_numStoping(self):
        return self.get_state_count('shutting-down')

    def get_state_count(self, stateName):
        try:
            response = boto3.client('ec2').describe_instances()
        except:
            print "exception while fetching instance description"
            return 0
        count = 0
        for res in response['Reservations']:
            for desc in res['Instances']:
                if (desc['State']['Name'] == stateName):
                    count += 1
        return count

import boto3
from botocore.exceptions import ClientError
import time
import requests

count = 9
ec2 = boto3.client('ec2')

# define network iterface
net_int = {'AssociatePublicIpAddress' : True}
net_ints = [net_int]

# do a dry run first to check permissions
try:
    response = ec2.run_instances(ImageId='ami-a8a5b3c8', \
                                      InstanceType='t2.micro', \
                                      KeyName='Cloud_Project', \
                                      MinCount=count, \
                                      MaxCount=count, \
                                      Monitoring={'Enabled': False}, \
                                      SecurityGroupIds=['sg-7f93b606'], \
                                      DryRun=False)
except ClientError as e:
    raise

publicip_list = []

for i in response['Instances']:
    # define EC2Instance object
    instance_id = i['InstanceId']
    print i['PrivateIpAddress']
    publicip = boto3.resource('ec2').Instance(instance_id).public_ip_address
    publicip_list.append(publicip)

time.sleep(40.0)

for ip in publicip_list:
    req_url = "http://" + str(ip) + ":8080/cloudimagerecognition"
    r = requests.get(req_url)
    print r

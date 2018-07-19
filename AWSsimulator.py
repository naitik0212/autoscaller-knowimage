import boto3
from botocore.exceptions import ClientError
import time
import requests
import urllib2

count = 5
ec2 = boto3.client('ec2')

# define network iterface
net_int = {'AssociatePublicIpAddress' : True}
net_ints = [net_int]

# do a dry run first to check permissions
try:
    response = ec2.run_instances(ImageId='**', \
                                      InstanceType='t2fmicro', \
                                      KeyName='Cloud_Project', \
                                      MinCount=count, \
                                      MaxCount=count, \
                                      Monitoring={'Enabled': False}, \
                                      SecurityGroupIds=['**'], \
                                      DryRun=False)
except ClientError as e:
    raise

publicip_list = []

for i in response['Instances']:
    # define EC2Instance object
    instance_id = i['InstanceId']
    publicip = boto3.resource('ec2').Instance(instance_id).public_ip_address
    publicip_list.append(publicip)

time.sleep(40.0)

for x in xrange(10):
    for ip in publicip_list:
        req_url = "http://" + str(ip) + ":8080/cloudimagerecognition"
        print time.time()
        var = True
        num_retries = 0
        while (var):
            try:
                r = requests.request(method="GET", url = req_url, allow_redirects=False)
                var = False
            except:
                print "failed! trying again..."
                var=True
                num_retries += 1
        print time.time()
        print num_retries
        print r.text
        time.sleep(2.0)

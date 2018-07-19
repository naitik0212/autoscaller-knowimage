import boto3


# terminate stray instances
ec2 = boto3.client('ec2')

response = ec2.describe_instances()
instance_ids = []

for res in response['Reservations']:
    for desc in res['Instances']:
        if desc['State']['Name'] == 'running':
            if (desc['InstanceId'] != 'i-***') and (desc['InstanceId'] != 'i-***'):
                instance_ids.append(desc['InstanceId'])
if instance_ids:
    ec2.terminate_instances(InstanceIds=instance_ids)


# clear the SQS queue
# sqs = boto3.client("sqs")
# sqs.purge_queue(QueueUrl='https://sqs.us-west-1.amazonaws.com/***/imagerecognition-request')
# sqs.purge_queue(QueueUrl='https://sqs.us-west-1.amazonaws.com/***/imagerecognition-response')

# start/restart the initial server
# initServer_state = boto3.resource('ec2').Instance('i-***').state['Name']
#
# if initServer_state == 'running':
#     ec2.reboot_instances(InstanceIds=['i-***'])
# else:
#     ec2.start_instances(InstanceIds=['i-***'])

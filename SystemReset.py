import boto3


# terminate stray instances
ec2 = boto3.client('ec2')

response = ec2.describe_instances()
instance_ids = []

for res in response['Reservations']:
    for desc in res['Instances']:
        if desc['State']['Name'] == 'running':
            if (desc['InstanceId'] != 'i-0b41b525cfed8e15b') and (desc['InstanceId'] != 'i-0000f5562e7630fae'):
                instance_ids.append(desc['InstanceId'])
if instance_ids:
    ec2.terminate_instances(InstanceIds=instance_ids)


# clear the SQS queue
# sqs = boto3.client("sqs")
# sqs.purge_queue(QueueUrl='https://sqs.us-west-1.amazonaws.com/791943463301/imagerecognition-request')
# sqs.purge_queue(QueueUrl='https://sqs.us-west-1.amazonaws.com/791943463301/imagerecognition-response')

# start/restart the initial server
# initServer_state = boto3.resource('ec2').Instance('i-05f04cca4008fb8ff').state['Name']
#
# if initServer_state == 'running':
#     ec2.reboot_instances(InstanceIds=['i-05f04cca4008fb8ff'])
# else:
#     ec2.start_instances(InstanceIds=['i-05f04cca4008fb8ff'])

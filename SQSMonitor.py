import boto3


class SQSMonitor(object):
    # A client to monitor Amazon SQS

    def __init__(self, url):
        # sqs sdk client
        self.sqs = boto3.client('sqs')

        # queue url
        self.url = url

    def num_messages(self):
        response = self.sqs.get_queue_attributes(QueueUrl=self.url, \
                                                 AttributeNames=['ApproximateNumberOfMessages'])
        num = response['Attributes']['ApproximateNumberOfMessages']
        print 'Number of requests in SQS: ' + str(num)
        return int(num)

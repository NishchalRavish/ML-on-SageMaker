s3_prefix = 'mlops_build_container'

import boto3
import re
import sagemaker as sage
from time import gmtime, strftime
import os
import numpy as np
import pandas as pd
from sagemaker import get_execution_role
from sagemaker.serializers import CSVSerializer
import itertools

role = get_execution_role()

sess = sage.Session()

WORK_DIRECTORY = 'model_container/data'

bucket = sagemaker.Session().default_bucket()
data_location = sess.upload_data(WORK_DIRECTORY,
                                 bucket=bucket,
                                 key_prefix=s3_prefix)

account = sess.boto_session.client('sts').get_caller_identity()['Account']
region = sess.boto_session.region_name
image_uri = '{}.dkr.ecr.{}.amazonaws.com/sagemaker-decision-trees:latest'.format(account,region)

tree = sage.estimator.Estimator(image_uri,
                                role,
                                instance_count=1,
                                instance_type='ml.m4.xlarge',
                                output_path="s3://{}/output".format(sess.default_bucket()),
                                sagemaker_session=sess)

file_location = data_location + '/iris.csv'
tree.fit(file_location)

predictor = tree.deploy(initial_instance_count=1,
                        instance_type='ml.m4.xlarge',
                        serializer=CSVSerializer())

shape=pd.read_csv(f"scikit-byoc/data/iris.csv", header=None)
shape.sample(3)

shape.drop(shape.columns[[0]],axis=1,inplace=True)
shape.sample(3)

a = [50*i for i in range(3)]
b = [40+i for i in range(10)]
indices = [i+j for i,j in itertools.product(a,b)]
test_data=shape.iloc[indices[:-1]]

print(predictor.predict(test_data.values).decode('utf-8'))

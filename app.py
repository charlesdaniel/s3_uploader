import os

os.environ["AWS_DATA_PATH"] = 'data/'
os.environ["AWS_CACERT"] = 'data/cacert.pem'

import s3_uploader

s3_uploader.main('~/s3_uploader.cfg')

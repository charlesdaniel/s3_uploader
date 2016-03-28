# S3 Uploader
##### by Charles Daniel

### Building the App

**Prerequisites**

- Python2.7 (hasn't been tested in anything else)
- Tkinter/ttk (should already be installed in a standard Python)
- Boto3
- Py2App

**Building the app**

Run `make`

This builds the app into the `dist/` directory.

**Running directly using Python**

`python s3_uploader.py`

### Configuration

There's a sample configuration file `s3_uploader.cfg.sample` that can be copies/used. Make sure you update the `aws_access_key_id` and `aws_secret_access_key` values. Add a list of s3 buckets for the pulldown by entering a comma separated list of bucket names as `s3_buckets`.

Alternatively you should be able to make a similar section called `[s3_uploader]` in any other file (including the `~/.aws/credentials`)
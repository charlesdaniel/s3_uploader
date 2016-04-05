# S3 Uploader
##### by Charles Daniel

### Introduction

This is a very simple S3 File Uploader app written in Python+Tkinter/ttk and uses Boto3 for the actual S3 interaction.
Additionally it uses py2app to create a standalone OSX app that can be launched by clicking an icon.
A configuration file can be used to specify the credentials as well as a list of buckets one should be uploading files into. It's mainly for giving it to non-technical people (along with a custom configuration file) so they can easily upload files to whatever bucket you like.

Each file uploading is done in a separate thread so the UI won't be blocked and one can upload any number of files concurrently. It's been tested with binary files of up to 62GB, haven't had a chance to try anything larger yet.

### Building the App

**Prerequisites**

- Python2.7 (hasn't been tested in anything else)
- Tkinter/ttk (should already be installed in a standard Python)
- Boto3
- Py2App

**Building a standalone app on OSX using py2app**

Run `make`

This builds the app into the `dist/` directory.
You'll want to make sure you have a configuration file located at `~/s3_uploader.cfg`.
Double click the new app in the `dist/` directory to launch it.

### Running directly using Python

You can run the s3_uploader directly using Python on the command line:

`python s3_uploader.py`

### Configuration

There's a sample configuration file `s3_uploader.cfg.sample` that can be copied and used as the starting point for the configurations. Make sure you update the `aws_access_key_id` and `aws_secret_access_key` values. Add a list of s3 buckets for the pulldown by entering a comma separated list of bucket names as `s3_buckets`.

Alternatively you should be able to make a similar section called `[s3_uploader]` in any other file (including the `~/.aws/credentials`)

By default the app looks for the `~/s3_uploader.cfg` file for the configurations, however you should be able to open a different configuration file by going to File > Open Config from the menubar.


### TODO

- Get things to work with py2exe or pyinstaller to build a windows app

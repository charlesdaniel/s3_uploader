#!/usr/bin/env python

from Tkinter import *
from ttk import *
import Tkconstants, tkFileDialog, tkSimpleDialog
import boto3
import botocore
from os.path import expanduser
import os
import thread
import ConfigParser
import webbrowser
import datetime


class Uploader(Frame):
    def __init__(self, root, filename, bucket_name, s3_filename):
        Frame.__init__(self, root)

        self._filename = filename
        self._bucket_name = bucket_name
        self._s3_filename = s3_filename

        # Used in percent & rate metric calculations
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._last_timestamp = None
        self._last_updated = None
        self._rate_samples = [ 0 for _i in xrange(0, 10) ]

        self._thread_should_exit = False

        s3_filelabel = Label(self, text="{}/{}".format(bucket_name, s3_filename))
        s3_filelabel.bind("<Button-1>", lambda e: webbrowser.open_new("https://s3.amazonaws.com/{}/{}".format(bucket_name, s3_filename)))
        s3_filelabel.grid(row=0, column=0, sticky=W, padx=10, pady=2)

        progress_frame = Frame(self)
        progress_frame.grid(row=0, column=1, padx=10, pady=2)

        self.progress = Progressbar(progress_frame, orient='horizontal', mode='determinate')
        self.progress.grid(row=0, column=0, columnspan=3, pady=0)

        self.percent_label = Label(progress_frame, text="?", font="Sans 8")
        self.percent_label.grid(row=1, column=2, padx=4, pady=0)

        self.rate_label = Label(progress_frame, text="?", font="Sans 8")
        self.rate_label.grid(row=1, column=0, padx=2, pady=0)

        self.rate_unit_label = Label(progress_frame, text="?", font="Sans 8")
        self.rate_unit_label.grid(row=1, column=1, padx=2, pady=0)

        self.cancel_button = Button(self, text="Cancel", command=self.cancel_transfer)
        self.cancel_button.grid(row=0, column=3, padx=10, pady=2)

    def update_progress(self, bytes_amount):
        # This method can be called many times a second. So we need to sample every so often (fractional seconds).
        # The rates are sampled and stored in a list then the average is used for the display.

        _now = datetime.datetime.now()
        self._seen_so_far += bytes_amount
        percentage = (self._seen_so_far / self._size) * 100
        percent = int(percentage)

        if (not self._last_updated) or ((_now - self._last_updated).total_seconds() > 0.25):
            self._last_updated = _now
            self.progress["value"] = percent
            self.percent_label["text"] = "{}%".format(percent)

            diff_secs = (_now - self._last_timestamp).total_seconds()
            self._last_timestamp = _now
            raw_rate = bytes_amount / diff_secs
            self._rate_samples.append(raw_rate)
            self._rate_samples.pop(0)

            #rate = max(self._rate_samples)
            rate = sum(self._rate_samples) / len(self._rate_samples)

            # Make the rate more human-readable
            sizes = ['KB','MB','GB','TB']
            rate_unit = 'B'
            for s in sizes:
                if (rate // 1024) > 0:
                    rate /= 1024
                    rate_unit = s
                else:
                    break

            self.rate_label["text"] = "{}".format(round(rate, 2))
            self.rate_unit_label["text"] = "{}/s".format(rate_unit)

        # If something set the _thread_should_exit flag then we should force the thread to exit
        # which will also kill the upload.
        if self._thread_should_exit:
            self.cancel_button["text"] = "Clear"
            thread.exit()

        # If we're done the upload at 100% then just convert the cancel button to Clear
        if percent >= 100:
            self.cancel_button["text"] = "Clear"

    def _do_transfer(self, aws_access_key_id, aws_secret_access_key):
        try:
            aws_session = boto3.session.Session(aws_access_key_id, aws_secret_access_key)
            cacert = os.environ.get('AWS_CACERT', None)
            s3 = aws_session.client('s3', verify=cacert)
            print "{} START TIME: {}".format(self._s3_filename, datetime.datetime.now())
            self._last_timestamp = datetime.datetime.now()
            s3.upload_file(self._filename, self._bucket_name, self._s3_filename, Callback=self.update_progress)
            print "{} END TIME: {}".format(self._s3_filename, datetime.datetime.now())
            self.percent_label["text"] = "100%"
            self.progress["value"] = 100
            self.cancel_button["text"] = "Clear"
        except botocore.exceptions.ClientError as e:
            print "ERROR ", e.message
            self.show_error([e.message])

    def show_error(self, errors):
        self.errors = Frame(self)
        for error in errors:
            Label(self.errors, text=error, style='Error.TLabel', font="Sans 8").pack(fill=BOTH)

        self.errors.grid(row=1, columnspan=4, padx=10)
        self.cancel_button["text"] = "Clear"

    def do_transfer(self, *args):
        thread.start_new_thread(self._do_transfer, args)

    def cancel_transfer(self):
        if self.cancel_button["text"] == "Cancel":
            # If the cancel button says "Cancel" then we want to set the exit flag to True
            self._thread_should_exit = True
        elif self.cancel_button["text"] == "Clear":
            # Otherwise if the cancel button says "Clear" we have to remove the upload frame
            self.grid_forget()


class S3FileUploader(Frame):
    def __init__(self, root, config_file):
        Frame.__init__(self, root)

        r = self.r = 0
        self.error_row = r
        padx = 10
        pady = 2

        r+=1
        Label(self, text="S3 Uploader", font="Sans 16 bold").grid(row=r, columnspan=2, pady=pady)

        r+=1
        Label(self, text="AWS AccessKeyID:").grid(row=r, sticky=W, padx=padx, pady=pady)
        self.aws_access_key_id = StringVar(self)
        Entry(self, textvariable=self.aws_access_key_id).grid(row=r, column=1, sticky=W, padx=padx, pady=pady)

        r+=1
        Label(self, text="AWS AccessSecretKey:").grid(row=r, sticky=W, padx=padx, pady=pady)
        self.aws_secret_access_key = StringVar(self)
        Entry(self, textvariable=self.aws_secret_access_key).grid(row=r, column=1, sticky=W, padx=padx, pady=pady)

        r+=1
        Label(self, text="File:").grid(row=r, sticky=W, padx=padx, pady=pady)
        self.file_button = Button(self, text='Choose Local File...', command=self.askopenfilename)
        self.file_button.grid(row=r, column=1, sticky=W, padx=padx, pady=pady)

        r+=1
        Label(self, text="S3 Bucket:").grid(row=r, sticky=W, padx=padx, pady=pady)
        self.s3_bucket = StringVar(self)
        self.s3_bucket_list = OptionMenu(self, self.s3_bucket)
        self.s3_bucket_list.grid(row=r, column=1, sticky=W, padx=padx, pady=pady)

        r+=1
        Label(self, text="S3 Filename:").grid(row=r, sticky=W, padx=padx, pady=pady)
        self.s3_name = StringVar(self)
        Entry(self, textvariable=self.s3_name).grid(row=r, column=1, sticky=W, padx=padx, pady=pady)

        r+=1
        Button(self, text='START UPLOAD', command=self.upload_to_s3).grid(row=r, columnspan=2, padx=padx, pady=pady)

        r+=1
        Separator(self, orient="horizontal").grid(row=r, columnspan=2, padx=padx, pady=pady)

        self.r = r
        
        self.errors = None
        self.config_file = config_file
        self.load_config(config_file)
        self.filename = None

    def prompt_load_config(self):
        initialdir = self.config_file if self.config_file else "~/"
        config_filename = tkFileDialog.askopenfilename(parent=self, initialdir=expanduser(initialdir), title="Choose config file") #, filetypes=[('cfg files', '.cfg')])
        if config_filename:
            self.load_config(config_filename)

    def load_config(self, config_file):
        self.clear_errors()
        config = ConfigParser.ConfigParser()
        config_file_handle = expanduser(config_file)
        config.read(config_file_handle)
        try:
            aws_access_key_id = config.get("s3_uploader", "aws_access_key_id")
            self.aws_access_key_id.set(aws_access_key_id)

            aws_secret_access_key = config.get("s3_uploader", "aws_secret_access_key")
            self.aws_secret_access_key.set(aws_secret_access_key)

            s3_buckets = config.get("s3_uploader", "s3_buckets")
            s3_buckets = s3_buckets.split(',')
            self.s3_bucket_list.set_menu(s3_buckets[0], *(s3_buckets))
            
            self.config_file = config_file
        except ConfigParser.NoSectionError:
            print "Failed to read Config File, missing section 's3_uploader'"
            self.show_errors([u"\u26A0 Failed to read Config File, missing section 's3_uploader'"])

    def askopenfilename(self):
        # define options for opening or saving a file
        self.file_opt = options = {}
        #options['defaultextension'] = '' #'.csv'
        #options['filetypes'] = [('all files', '.*'), ('text files', '.csv')]
        options['initialdir'] = expanduser("~")
        #options['initialfile'] = ''
        options['parent'] = self
        options['title'] = 'Choose File to upload'

        # get filename
        self.filename = tkFileDialog.askopenfilename(**self.file_opt)

        # open file on your own
        if self.filename:
            self.file_button["text"] = self.filename

    def show_errors(self, errors):
        self.errors = Frame(self)
        for error in errors:
            Label(self.errors, text=error, style='Error.TLabel').pack(fill=BOTH)

        self.errors.grid(row=self.error_row, columnspan=2, pady=20)

    def clear_errors(self):
        if self.errors:
            self.errors.destroy()
            self.errors = None

    def upload_to_s3(self):
        self.clear_errors()

        aws_access_key_id = self.aws_access_key_id.get()
        aws_secret_access_key = self.aws_secret_access_key.get()
        filename = self.filename
        bucket = self.s3_bucket.get()
        name = self.s3_name.get()

        errors = []
        if not aws_access_key_id:
            errors.append(u"\u26A0 AWS Access Key ID is required")
        if not aws_secret_access_key:
            errors.append(u"\u26A0 AWS Access Secret Key is required")
        if not filename:
            errors.append(u"\u26A0 A File must be chosen for upload")
        if not bucket:
            errors.append(u"\u26A0 Choose an S3 bucket to upload the file to")
        if not name:
            errors.append(u"\u26A0 Enter a S3 filename to upload the file as")

        if errors:
            self.show_errors(errors)
            return

        self.r += 1
        up = Uploader(self, filename, bucket, name)
        up.grid(row=self.r, columnspan=2, sticky=NSEW)

        up.do_transfer(aws_access_key_id, aws_secret_access_key)


class AboutWin(tkSimpleDialog.Dialog):
    def __init__(self, root):
        self._parent = root

    def show(self):
        tkSimpleDialog.Dialog.__init__(self, self._parent, "About S3 Uploader")

    def body(self, master):
        fr = Frame(master)
        Label(fr, text="S3 Uploader", font="Sans 14 bold").pack(padx=50)
        Label(fr, text="by Charles Daniel", font="Sans 10").pack(padx=50)
        Button(fr, text="OK", command=self.destroy).pack(padx=50, pady=10)
        fr.pack()

    def destroy(self):
        tkSimpleDialog.Dialog.destroy(self)

    def buttonbox(self):
        pass


def main(config_file):
    root = Tk()
    s = Style(root)
    s.configure('Error.TLabel', foreground='red', background='yellow')
    s.configure('.', padx=10, pady=10)

    root.title("S3 File Uploader")
    root['background'] = '#ececec'

    about_win = AboutWin(root)
    s3uploader_win = S3FileUploader(root, config_file)
    s3uploader_win.pack()

    menubar = Menu(root)
    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="About", command=about_win.show)
    filemenu.add_separator()
    filemenu.add_command(label="Open Config...", command=s3uploader_win.prompt_load_config)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="S3Uploader", menu=filemenu)
    root.config(menu=menubar)

    root.mainloop()

if __name__=='__main__':
    main("~/s3_uploader.cfg")

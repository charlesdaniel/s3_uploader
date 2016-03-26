#!/usr/bin/env python

from Tkinter import *
from ttk import *
import Tkconstants, tkFileDialog
import boto3
from os.path import expanduser
import os
import thread

class Uploader(Frame):
    def __init__(self, root, filename):
        Frame.__init__(self, root)

        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0

        self._thread_should_exit = False

        Label(self, text="{}".format(filename)).grid(row=0, column=0, sticky=W)
        self.progress = Progressbar(self, orient='horizontal', mode='determinate')
        self.progress.grid(row=0, column=1, padx=10)

        self.cancel_button = Button(self, text="Cancel", command=self.cancel_transfer)
        self.cancel_button.grid(row=0, column=2, padx=5)

    def update_progress(self, bytes_amount):
        self._seen_so_far += bytes_amount
        percentage = (self._seen_so_far / self._size) * 100
        sys.stdout.write("%s %s / %s (%.2f%%)" % (self._filename, self._seen_so_far, self._size, percentage))
        sys.stdout.flush()

        self.percent = int(percentage)
        print "updating progressbar"
        self.progress["value"] = self.percent
        if self._thread_should_exit:
            print "EXITING THREAD"
            self.cancel_button["text"] = "Clear"
            thread.exit()

        if self.percent >= 100:
            self.cancel_button["text"] = "Clear"

    def _do_transfer(self, aws_key_id, aws_secret_key, filename, bucket, key):
        aws_session = boto3.session.Session(aws_key_id, aws_secret_key)
        s3 = aws_session.client('s3')
        s3.upload_file(filename, bucket, key, Callback=self.update_progress)

    def do_transfer(self, *args):
        thread.start_new_thread(self._do_transfer, args)

    def cancel_transfer(self):
        print "CANCELING TRANSFER"
        if self.cancel_button["text"] == "Cancel":
            self._thread_should_exit = True
        elif self.cancel_button["text"] == "Clear":
            self.grid_forget()


class S3FileUploader(Frame):

    def __init__(self, root):
        Frame.__init__(self, root)
        root.title("S3 File Uploader")
        root.geometry('{}x{}'.format(400, 400))

        # options for buttons
        button_opt = {'fill': Tkconstants.BOTH, 'padx': 5, 'pady': 5}

        # define buttons
        r = self.r = 0
        Label(self, text="S3 Uploader").grid(row=r, columnspan=2)

        r+=1
        Label(self, text="AWS AccessKeyID:").grid(row=r, sticky=W)
        self.aws_access_key_id = StringVar(self)
        Entry(self, textvariable=self.aws_access_key_id).grid(row=r, column=1, sticky=W)

        r+=1
        Label(self, text="AWS AccessSecretKey:").grid(row=r, sticky=W)
        self.aws_access_secret_key = StringVar(self)
        Entry(self, textvariable=self.aws_access_secret_key).grid(row=r, column=1, sticky=W)

        r+=1
        Label(self, text="File").grid(row=r, sticky=W)
        self.file_button = Button(self, text='Choose Local File...', command=self.askopenfilename)
        self.file_button.grid(row=r, column=1, sticky=W)

        r+=1
        Label(self, text="S3 Bucket").grid(row=r, sticky=W)
        self.s3_bucket = StringVar(self)
        self.s3_bucket.set("public")
        OptionMenu(self, self.s3_bucket, "org.cdfx.foobar", "secured", "secured", "public").grid(row=r, column=1, sticky=W)

        r+=1
        Label(self, text="S3 Filename").grid(row=r, sticky=W)
        self.s3_name = StringVar(self)
        Entry(self, textvariable=self.s3_name).grid(row=r, column=1, sticky=W)

        r+=1
        Button(self, text='START UPLOAD', command=self.upload_to_s3).grid(row=r, columnspan=2)

        r+=1
        Separator(self, orient="horizontal").grid(row=r, columnspan=2)

        self.r = r

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
            print "FILENAME TO OPEN ", self.filename
            self.file_button["text"] = self.filename

    def upload_to_s3(self):
        aws_key_id = self.aws_access_key_id.get()
        aws_secret_key = self.aws_access_secret_key.get()
        filename = self.filename
        bucket = self.s3_bucket.get()
        name = self.s3_name.get()

        self.r += 1
        up = Uploader(self, filename)
        up.grid(row=self.r, columnspan=2, sticky=NSEW)

        up.do_transfer(aws_key_id, aws_secret_key, filename, bucket, name)

if __name__=='__main__':
    root = Tk()
    root.height = 500
    root.width = 500
    S3FileUploader(root).pack()
    root.mainloop()

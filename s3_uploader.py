#!/usr/bin/env python

from Tkinter import *
from ttk import *
import Tkconstants, tkFileDialog, tkSimpleDialog
import boto3
from os.path import expanduser
import os
import thread
import ConfigParser

class Uploader(Frame):
    def __init__(self, root, filename):
        Frame.__init__(self, root)

        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0

        self._thread_should_exit = False

        Label(self, text="{}".format(filename)).grid(row=0, column=0, sticky=W, padx=10, pady=2)
        self.progress = Progressbar(self, orient='horizontal', mode='determinate')
        self.progress.grid(row=0, column=1, padx=10, pady=2)

        self.percent_label = Label(self, text="?", font="Sans 8")
        self.percent_label.grid(row=0, column=2, padx=4, pady=2)

        self.cancel_button = Button(self, text="Cancel", command=self.cancel_transfer)
        self.cancel_button.grid(row=0, column=3, padx=10, pady=2)

    def update_progress(self, bytes_amount):
        self._seen_so_far += bytes_amount
        percentage = (self._seen_so_far / self._size) * 100

        self.percent = int(percentage)
        self.progress["value"] = self.percent
        self.percent_label["text"] = "{}%".format(self.percent)
        if self._thread_should_exit:
            self.cancel_button["text"] = "Clear"
            thread.exit()

        if self.percent >= 100:
            self.cancel_button["text"] = "Clear"

    def _do_transfer(self, aws_access_key_id, aws_secret_access_key, filename, bucket, key):
        aws_session = boto3.session.Session(aws_access_key_id, aws_secret_access_key)
        cacert = os.environ.get('AWS_CACERT', None)
        s3 = aws_session.client('s3', verify=cacert)
        s3.upload_file(filename, bucket, key, Callback=self.update_progress)

    def do_transfer(self, *args):
        thread.start_new_thread(self._do_transfer, args)

    def cancel_transfer(self):
        if self.cancel_button["text"] == "Cancel":
            self._thread_should_exit = True
        elif self.cancel_button["text"] == "Clear":
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
        self.s3_bucket.set("public")
        self.s3_bucket_list = OptionMenu(self, self.s3_bucket, "org.cdfx.foobar", "secured", "secured", "public")
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
        
        self.config_file = config_file
        self.load_config(config_file)
        self.filename = None

    def prompt_load_config(self):
        initialdir = self.config_file if self.config_file else "~/"
        config_filename = tkFileDialog.askopenfilename(parent=self, initialdir=expanduser(initialdir), title="Choose config file") #, filetypes=[('cfg files', '.cfg')])
        if config_filename:
            self.load_config(config_filename)

    def load_config(self, config_file):
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

    def upload_to_s3(self):
        if hasattr(self, 'errors'):
            self.errors.grid_forget()

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
        up = Uploader(self, filename)
        up.grid(row=self.r, columnspan=2, sticky=NSEW)

        up.do_transfer(aws_access_key_id, aws_secret_access_key, filename, bucket, name)


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

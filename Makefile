S3Uploader.app: dist/app.app
	cp -R dist/app.app ./S3Uploader.app

dist/app.app: data s3_uploader.py app.py
	python setup.py py2app

data:
	cp -R /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/botocore/data data
	cp -R /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/botocore/vendored/requests/cacert.pem data/

clean:
	rm -rf data dist build *.pyc S3Uploader.app

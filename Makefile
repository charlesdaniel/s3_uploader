dist/S3Uploader.app: data s3_uploader.py app.py
	python setup.py py2app

data:
	cp -R /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/botocore/data data
	cp -R /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/botocore/vendored/requests/cacert.pem data/

clean:
	-rm -f *.pyc
	-rm -rf data
	-rm -rf build
	-rm -rf dist

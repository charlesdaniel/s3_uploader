
dist/S3Uploader.app: dependencies data s3_uploader.py app.py
	python setup.py py2app

dependencies:
	pip install -r pip-requirements.txt

data: dependencies
	botocore_dir=$$(python -c 'import botocore; print botocore.__path__[0]'); \
	echo "BOTOCORE $${botocore_dir}"; \
	cp -R $${botocore_dir}/data data; \
	cp -R $${botocore_dir}/vendored/requests/cacert.pem data/

clean:
	-rm -f *.pyc
	-rm -rf data
	-rm -rf build
	-rm -rf dist

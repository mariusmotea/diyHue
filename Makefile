WD=$(shell pwd)

### Env ###
env:
	virtualenv -p `which python3` env
	env/bin/pip install -r requirements.txt
	env/bin/pip install -r test_requirements.txt
	env/bin/python setup.py develop
	echo "You can now run 'source env/bin/activate'"

### Test ###
test:
	env/bin/tox

### Doc ###
doc-gen:
	cd doc && make html

doc-clean:
	cd doc && make clean

doc-update-refs:
	rm -rf doc/source/refs/
	sphinx-apidoc -M -f -e -o doc/source/refs/ huebridgeemulator/

### https ###
https/dh.pem:
	mkdir -p https
	cd https && openssl dhparam -out dh.pem 1028

https/csr.pem:
	mkdir -p https
	cd https && openssl req -nodes -new -newkey rsa:4096 -out csr.pem -sha256

_https/keys: https/csr.pem
	mkdir -p https
	cd https && openssl req -x509 -newkey rsa:4086 -keyout key.pem -out cert.pem -days 3650 -nodes -sha256

https/cert.pem: _https/keys

https/key.pem: _https/keys

https_generate: https/dh1028.pem
	mkdir -p https
	cd https && openssl req -nodes -new -newkey rsa:4096 -out csr.pem -sha256
	cd https && openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 3650 -nodes -sha256

### Web UI ###
gen_ui:
	echo "Not implemented Yet"

### RUN ###
run_debug: docker_run_httpd
	env/bin/huebridgeemulator  -c config.json -l DEBUG

### Docker ###
docker_build:
	sudo rm -rf `find . -name  __pycache__`
	docker build -t hue-bridge-emulator .

docker_irun:
	docker run -v $(WD)/config.json:/config.json --rm --name hbe --net=host -it --entrypoint=bash hue-bridge-emulator

docker_run:
	docker run -it -v $(WD)/config.json:/config.json --rm --name hbe --net=host hue-bridge-emulator

docker_run_httpd: https/dh.pem _https/keys
	docker run -it -d --rm --name hbe-http -v `pwd`/https:/etc/nginx/external/ --net=host marvambass/nginx-ssl-secure

docker_run_http: https/dh.pem _https/keys
	docker run -it -d --rm --name hbe-http -v `pwd`/https:/etc/nginx/external/ --net=host marvambass/nginx-ssl-secure

docker_stop:
	docker kill hbe-http || true
	docker kill hbe || true

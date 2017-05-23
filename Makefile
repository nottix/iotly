init:
	pip install -r requirements.txt

install:
	sudo cp script/iotly.service /lib/systemd/system/iotly.service
	sudo chmod 644 /lib/systemd/system/iotly.service
	sudo systemctl daemon-reload
	sudo systemctl enable iotly.service

test:
	nosetests tests

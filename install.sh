#!/bin/bash
virtualenv flask
flask/bin/pip install flask pika
flask/bin/pip install git+https://github.com/msiemens/tinydb.git
chmod a+x api.py db.py

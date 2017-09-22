#!flask/bin/python
from flask import Flask, jsonify, request, abort
import uuid
import pika
import threading
import time


app = Flask(__name__)
client = None
PENDING = 0
A_QUEUE = 'a_to_c'


#######
# API #
#######
@app.route('/api/v1.0/values/<string:key>', methods=['GET'])
def request_value(key):
    _send_get_req(key)
    return "GET request for '" + key + "' send.\n" + "Location: " + \
        "127.0.0.1:5000/api/v1.0/value/" + key + "\n", 303


@app.route('/api/v1.0/value/<string:key>', methods=['GET'])
def get_value(key):
    if client:
        if key not in client.responses:
            abort(404)
        value = client.responses[key]
        if value == PENDING:
            return "Pending...\n"
        if value is None:
            del client.responses[key]
            return "Key '" + key +"' not in database.\n"
        del client.responses[key]
        return jsonify({key : value})
    return "Something went wrong.\n"


@app.route('/api/v1.0/value', methods=['POST'])
def post_value():
    if request.method == 'POST':
        key = request.form['key']
        value = request.form['value']
        if key and value:
            _send_post_req(key, value)     
            return "POST request for '" + key + ":" + value + "' send.\n"
        else:
            missing = (" key" if not key else "") + (" value" if not value else "") 
            return "Missing parameters:" + missing + "\n"
    else:
        abort(404)


#############
# RABBIT_MQ #
#############
def _send_get_req(key):
    client.responses[key] = PENDING
    client.call(key)


def _send_post_req(key, value):
    body = str(key) + ":" + str(value)
    client.call(body)


class Client(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(self.on_response,
            no_ack=True,
            queue=self.callback_queue)
        self.responses = {}
        self.thread = None


    def worker(self):
        while True:
            self.connection.process_data_events(time_limit=1)
            time.sleep(1)


    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            response = body.decode('utf-8').split(":")
            if len(response) == 1 or response[1] == "":
                self.responses[response[0]] = None
            else:
                self.responses[response[0]] = response[1]


    def call(self, body):
        self.corr_id = str(uuid.uuid4())
        properties = pika.BasicProperties(reply_to = self.callback_queue,
            correlation_id = self.corr_id) 
        self.channel.basic_publish(exchange='',
            routing_key=A_QUEUE,
            properties=properties,
            body=body)
        if self.thread is None:
            self.thread = threading.Thread(target=self.worker)
            self.thread.deamon = True
            self.thread.start()


#############
# START APP #
#############
if __name__ == '__main__':
    client = Client()
    app.run(debug=True, port=5000)
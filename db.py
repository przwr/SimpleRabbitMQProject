#!flask/bin/python
from flask import Flask, jsonify, request, abort
from tinydb import TinyDB, Query
import pika
import threading
import time


app = Flask(__name__)
db = TinyDB('db.json')
started = True
A_QUEUE = 'a_to_c'


#######
# API #
#######
@app.route('/api/v1.0/values/<string:key>', methods=['GET'])
def get_value(key):
    value = _get_from_database(key)
    if value is None:
        abort(404)
    return jsonify({key: value})


@app.route('/api/v1.0/value', methods=['POST'])
def post_value():
    if request.method == 'POST':
        key = request.form['key']
        value = request.form['value']
        if key and value:
            _add_to_database(key, value)
        else:
        	missing = (" key" if not key else "") + (" value" if not value else "") 
        	return "Missing parameters:" + missing + "\n"
    else:
        abort(404)


#############
# RABBIT_MQ #
#############
def _get_callback(ch, method, properties, body):
    req = body.decode("utf-8").split(":")
    if len(req) == 1:
        value = _get_from_database(req[0])
        if value is None:
            response = str(req[0]) + ":"
        else:
            response = str(req[0]) + ":" + str(value)
        _send_push_req(ch, method, properties, response)
    else:    
        _send_ack_req(ch, method, properties, req[0], req[1])


def _send_push_req(channel, method, properties, body):
    channel.basic_publish(exchange='',
    	routing_key=properties.reply_to,
    	properties=pika.BasicProperties(correlation_id = properties.correlation_id),
    	body=str(body))
    channel.basic_ack(delivery_tag = method.delivery_tag)


def _send_ack_req(channel, method, properties, key, value):    
    channel.basic_publish(exchange='',
    	routing_key=properties.reply_to,
    	properties=pika.BasicProperties(correlation_id = properties.correlation_id),
    	body="")
    channel.basic_ack(delivery_tag = method.delivery_tag)
    _add_to_database(key, value)


def _worker():
	try:
		connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
		channel = connection.channel()
		channel.queue_declare(queue=A_QUEUE)
		channel.basic_qos(prefetch_count=1)
		channel.basic_consume(_get_callback, queue=A_QUEUE)
		while started:
			connection.process_data_events(time_limit=1)
	except KeyboardInterrupt:
		pass


def _start_listener():
	thread = threading.Thread(target=_worker)
	thread.deamon = True
	thread.start()


############
# DATABASE #
############
def _add_to_database(key, value):
    from tinydb.operations import set
    query = Query()
    keys = db.search(query.key == key)
    if len(keys):
        db.update(set('value', value), query.key == key)
    else:
        db.insert({'key': key, 'value': value})


def _get_from_database(key):
    keys = db.search(Query().key == key)
    if len(keys):
        return keys[0]['value']
    else:
        return None


#############
# START APP #
#############
if __name__ == '__main__':
    _start_listener()
    app.run(debug=True, port=5001)
    started = False
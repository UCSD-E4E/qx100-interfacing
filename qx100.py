#!/usr/bin/env python

"""QX100 interfacing code for python"""

import json
import requests
import threading

import time

def get_payload(method, params):
    return {
	"method": method,
	"params": params,
	"id": 1,
	"version": "1.0"
    }

def take_picture():
    payload = get_payload("actTakePicture", [])
    headers = {'Content-Type': 'application/json'}
    response = requests.post('http://10.0.0.1:10000/sony/camera', data=json.dumps(payload), headers=headers)
    url = response.json()['result']
    strurl = str(url[0][0])
    return strurl

def get_event():
    payload = get_payload("getEvent", [False])
    headers = {'Content-Type': 'application/json'}
    response = requests.post('http://10.0.0.1:10000/sony/camera', data=json.dumps(payload), headers=headers)

    return response

def get_picture(url, filename):
    response = requests.get(url)
    chunk_size = 1024
    with open(filename, 'wb') as fd:
	for chunk in response.iter_content(chunk_size):
	    fd.write(chunk)

### LIVEVIEW STUFF
def start_liveview():
    payload = get_payload("startLiveview", [])
    headers = {'Content-Type': 'application/json'}
    response = requests.post('http://10.0.0.1:10000/sony/camera', data=json.dumps(payload), headers=headers)
    url = response.json()['result']
    strurl = str(url[0])
    return strurl

def open_stream(url):
    return requests.get(url, stream=True)

def decode_frame(data):

    # decode packet header
    start = ord(data.raw.read(1))
    if(start != 0xFF):
	print 'bad start byte\nexpected 0xFF got %x'%start
	return
    pkt_type = ord(data.raw.read(1))
    if(pkt_type != 0x01):
	print 'not a liveview packet'
	return
    frameno = int(data.raw.read(2).encode('hex'), 16)
    timestamp = int(data.raw.read(4).encode('hex'), 16)

    decode_frame.last_time = decode_frame.current_time
    decode_frame.current_time = time.time()
    print decode_frame.current_time - decode_frame.last_time

    # decode liveview header
    start = int(data.raw.read(4).encode('hex'), 16)
    if(start != 0x24356879):
	print 'expected 0x24356879 got %x'%start
	return
    jpg_size = int(data.raw.read(3).encode('hex'), 16)
    pad_size = ord(data.raw.read(1))
    # read out the reserved header
    data.raw.read(4)
    fixed_byte = ord(data.raw.read(1))
    if(fixed_byte is not 0x00):
	print 'expected 0x00 got %x'%fixed_byte
	return
    data.raw.read(115)

    # read out the jpg
    jpg_data = data.raw.read(jpg_size)
    data.raw.read(pad_size)

    return jpg_data
    
decode_frame.current_time = 0
decode_frame.last_time = 0

s = start_liveview()
data = open_stream(s)
while True:
    jpg = decode_frame(data)
    f = open('/tmp/pic.jpg', 'w')
    f.write(jpg)
    f.close()
data.raw.close()

#!/usr/bin/python
import docker
import json
import socket
from docker import Client
import json
import etcd
import time
from daemon import runner
import sys
import getopt

def get_container_key(json): 
	c = Client(base_url='unix://var/run/docker.sock')
	b=str(json['Names'][0])
	container_name=b.lstrip('/')
	for k in json['Ports']:
		if k.has_key('PublicPort') == True:
			container_port=k['PublicPort']
	Host_IP=get_my_ip()
	container_inspect=c.inspect_container(container_name)
	Env=container_inspect['Config']['Env']
	virtual_host=get_virtual_host(Env)
	container_key={'container_name':container_name,'Host_IP':Host_IP,'container_port':container_port,'virtual_host':virtual_host}
	return container_key

def get_my_ip():
    """
    Returns the actual ip of the local machine.
    This code figures out what source address would be used if some traffic
    were to be sent out to some well known address on the Internet. In this
    case, a Google DNS server is used, but the specific address does not
    matter much.  No traffic is actually sent.
    """
    try:
        csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        csock.connect(('8.8.8.8', 80))
        (addr, port) = csock.getsockname()
        csock.close()
        return addr
    except socket.error:
        return "127.0.0.1"

def get_virtual_host(array):
	if array != None:
		for i in array:
			if 'VIRTUAL_HOST' in i:
				k=i.split('=')
				vh=str(k[1])
				return vh

def get_config():
	opts, args = getopt.getopt(sys.argv[1:], "hl:n:p:")
	locate = '/myapp'
	node = '127.0.0.1'
	port = 2379
	for op, value in opts:
		if op == "-l":
			locate = value
		elif op == '-n':
			node = value
		elif op == '-p':
			port == value
		elif op == '-h':
			print_help()
			sys.exit()
	return {'locate':locate,'node':node,'port':port}
def print_help():
    print('''usage: container_discover.py [OPTION]...

options:
-h,                    show this help message and exit
-l  		       locate in your etcd to put value
-n                     etcd nodes host
-p                     etcd nodes port
''')




	
def main():				
	while True:
		c = Client(base_url='unix://var/run/docker.sock')

		containers=c.containers()
		config=get_config()
		print config
		locate=config['locate']
		host=config['node']
		port=config['port']
		client = etcd.Client(
	             host=host,
	             port=port,
	             allow_reconnect=True,)
		for k in containers:
			a= get_container_key(k)
			if a['virtual_host']!= None:
				locate_write=locate+'/'+a['virtual_host']+'/'+a['container_name']
				value_write={"address":a['Host_IP'],"port":a['container_port']}
				value_write_json=json.dumps(value_write)
				client.write(locate_write,value_write_json,ttl=64)
				print time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))+" put "+locate_write+" value "+value_write_json
		time.sleep(5)

if __name__ == "__main__":
    main()


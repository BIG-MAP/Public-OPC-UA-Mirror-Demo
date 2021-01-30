# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import logging
import asyncio
import sys
sys.path.insert(0, "..")

from asyncua import ua, Server, Client
from asyncua.common.methods import uamethod


#logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.ERROR)
_logger = logging.getLogger('asyncua')

update_period_s = 5

@uamethod
def func(parent, value):
    return value * 2

shared = type('', (), {})()
shared.value = 0

async def main():
    task1 = asyncio.create_task(main_server_1())
    task2 = asyncio.create_task(main_server_2())
    task3 = asyncio.create_task(client_1_1(shared))
    task4 = asyncio.create_task(client_1_2(shared))
    await task1
    await task2
    await task3
    await task4
    
    #await asyncio.gather(client_1_1(shared_value), client_1_2(shared_value))
    
async def main_server_1():
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint('opc.tcp://0.0.0.0:4840/freeopcua/server/')

    # setup our own namespace, not really necessary but should as spec
    uri = 'http://examples.freeopcua.github.io'
    idx = await server.register_namespace(uri)

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root
    myobj = await server.nodes.objects.add_object(idx, 'MyObject')
    myvar = await myobj.add_variable(idx, 'MyVariable', 6.7)
    # Set MyVariable to be writable by clients
    await myvar.set_writable()
    await server.nodes.objects.add_method(ua.NodeId('ServerMethod', 2), ua.QualifiedName('ServerMethod', 2), func, [ua.VariantType.Int64], [ua.VariantType.Int64])
    _logger.info('Starting server!')
    async with server:
        while True:
            await asyncio.sleep(update_period_s)
            new_val = await myvar.get_value() + 0.1
            _logger.info('[SERVER] Set value of %s to %.1f', myvar, new_val)
            await myvar.write_value(new_val)
            
async def main_server_2():
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint('opc.tcp://0.0.0.0:4841/freeopcua/server2/')

    # setup our own namespace, not really necessary but should as spec
    uri = 'http://examples.freeopcua.github.io'
    idx = await server.register_namespace(uri)

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root
    myobj = await server.nodes.objects.add_object(idx, 'MyObject2')
    myvar = await myobj.add_variable(idx, 'MyVariable2', 1.7)
    # Set MyVariable to be writable by clients
    await myvar.set_writable()
    await server.nodes.objects.add_method(ua.NodeId('ServerMethod2', 2), ua.QualifiedName('ServerMethod2', 2), func, [ua.VariantType.Int64], [ua.VariantType.Int64])
    _logger.info('Starting server2!')
    async with server:
        while True:
            await asyncio.sleep(update_period_s)
            new_val = await myvar.get_value()# + 0.1
            _logger.info('[SERVER2] Set value of %s to %.1f', myvar, new_val)
            #await myvar.write_value(new_val)
            
async def client_1_1(shared):
    url = 'opc.tcp://localhost:4840/freeopcua/server/'
    url2 = 'opc.tcp://localhost:4841/freeopcua/server/'
    # url = 'opc.tcp://commsvr.com:51234/UA/CAS_UA_Server'
    async with Client(url=url) as client:
        # Client has a few methods to get proxy to UA nodes that should always be in address space such as Root or Objects
        # Node objects have methods to read and write node attributes as well as browse or populate address space
        _logger.info('Children of root are: %r', await client.nodes.root.get_children())

        uri = 'http://examples.freeopcua.github.io'
        idx = await client.get_namespace_index(uri)
        # get a specific node knowing its node id
        # var = client.get_node(ua.NodeId(1002, 2))
        # var = client.get_node("ns=3;i=2002")
        var = await client.nodes.root.get_child(["0:Objects", f"{idx}:MyObject", f"{idx}:MyVariable"])
        while True:
            await asyncio.sleep(update_period_s)
            shared.value = await var.read_value()
            print("[Client1] Read My variable", var, shared.value)
        # print(var)
        # await var.read_data_value() # get value of node as a DataValue object
        # await var.read_value() # get value of node as a python builtin
        # await var.write_value(ua.Variant([23], ua.VariantType.Int64)) #set node value using explicit data type
        # await var.write_value(3.9) # set node value using implicit data type
async def client_1_2(shared):
    url = 'opc.tcp://localhost:4840/freeopcua/server/'
    url2 = 'opc.tcp://localhost:4841/freeopcua/server/'
    # url = 'opc.tcp://commsvr.com:51234/UA/CAS_UA_Server'
    async with Client(url=url2) as client2:
        _logger.info('Children of root are: %r', await client2.nodes.root.get_children())

        uri = 'http://examples.freeopcua.github.io'
        idx = await client2.get_namespace_index(uri)
        # get a specific node knowing its node id
        # var = client.get_node(ua.NodeId(1002, 2))
        # var = client.get_node("ns=3;i=2002")
        var = await client2.nodes.root.get_child(["0:Objects", f"{idx}:MyObject2", f"{idx}:MyVariable2"])
        while True:
            await asyncio.sleep(update_period_s)
            await var.write_value(shared.value)
            value = await var.read_value()
            print("[Client2] Write My variable", var, value)


if __name__ == '__main__':
    asyncio.run(main())
    #await main()

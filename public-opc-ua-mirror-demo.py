# -*- coding: utf-8 -*-
"""
Public OPC UA Mirror Demo

Creates following setup:
    
(ext. Client* <->) Physical Device <-> Mirror Server <-> Virtual Device (<-> ext. Client*)

*not part of this code, use e. g. a GUI client

"""
import logging
import asyncio
import sys
sys.path.insert(0, "..")

from asyncua import Server, Client
import time
import math

logging.basicConfig(level=logging.ERROR)
_logger = logging.getLogger('asyncua')

#update period for servers 1
update_period_s = 1

#create some async running task to emulate multiple servers and clients in a single program
async def main():
    task1 = asyncio.create_task(main_physical_device())
    task2 = asyncio.create_task(main_virtual_device())
    task3 = asyncio.create_task(main_mirror_client_1(shared))
    task4 = asyncio.create_task(main_mirror_client_2(shared))
    await task1
    await task2
    await task3
    await task4
    
    #await asyncio.gather(client_1_1(shared_value), client_1_2(shared_value))
    
async def main_physical_device():
    #this code runs on the the physical device
    
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint('opc.tcp://0.0.0.0:4840/physical/server/')

    # setup our own namespace, not really necessary but should as spec
    uri = 'http://examples.freeopcua.github.io'
    idx = await server.register_namespace(uri)

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root
    component = await server.nodes.objects.add_object(idx, 'Component')
    sensor_value = await component.add_variable(idx, 'SensorValue', 6.7)
    command_id = await component.add_variable(idx, 'CommandID', 0)
    # Set CommandID to be writable by clients
    await command_id.set_writable()
    
    _logger.info('Starting Physical Device Server!')
    async with server:
        while True:
            await asyncio.sleep(update_period_s)
            #read command id
            new_command_val = await command_id.read_value()
            print('[Physical Device] value of %s is %.1f', command_id, new_command_val)
            #generate new sensor value
            new_sensor_val = math.sin(new_command_val*time.time())
            print('[Physical Device] Set value of %s to %.1f', sensor_value, new_sensor_val)
            await sensor_value.write_value(new_sensor_val)

            
async def main_virtual_device():
    #this code runs on the the cloud server
    
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint('opc.tcp://0.0.0.0:4841/virtual/server/')

    # setup our own namespace, not really necessary but should as spec
    uri = 'http://examples.freeopcua.github.io'
    idx = await server.register_namespace(uri)

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root
    component = await server.nodes.objects.add_object(idx, 'Component')
    sensor_value = await component.add_variable(idx, 'SensorValue', 6.7)
    command_id = await component.add_variable(idx, 'CommandID', 0)
    # Set CommandID to be writable by clients
    await command_id.set_writable()
     # Set SensorValue to be writable by clients (for the mirror server)
    await sensor_value.set_writable()
    
    _logger.info('Starting Virtual Device Server!')
    async with server:
        while True:
            await asyncio.sleep(update_period_s)
            #update values
            new_sensor_val = await sensor_value.read_value()
            print('[Virtual Device] value of %s is %.1f', sensor_value, new_sensor_val)
            new_command_val = await command_id.read_value()
            print('[Virtual Device] value of %s is %.1f', command_id, new_command_val)
  
#create a shared object for the internal data exchange in client_1
shared = type('', (), {})()
shared.sensor_value = 0  
shared.command_id = 0         
  
async def main_mirror_client_1(shared):
    #this client runs on an (local) mirror server together with main_mirror_client_2 and is connected to the physical device server
    
    url = 'opc.tcp://localhost:4840/physical/server/'

    async with Client(url=url) as client:

        uri = 'http://examples.freeopcua.github.io'
        idx = await client.get_namespace_index(uri)

        sensor_value = await client.nodes.root.get_child(["0:Objects", f"{idx}:Component", f"{idx}:SensorValue"])
        command_id = await client.nodes.root.get_child(["0:Objects", f"{idx}:Component", f"{idx}:CommandID"])
        while True:
            await asyncio.sleep(update_period_s)
            #read sensor value from physical device
            shared.sensor_value = await sensor_value.read_value()
            print("[Mirror_Client1] Read from physical ", sensor_value, shared.sensor_value)
            #write command id to physical device
            await command_id.write_value(shared.command_id)
            new_command_value = await command_id.read_value()
            print("[Mirror_Client1] Write to physical ", command_id, new_command_value)
            
async def main_mirror_client_2(shared):
    #this client runs on an (local) mirror server together with main_mirror_client_1 and is connected to the virtual device server
    
    url = 'opc.tcp://localhost:4841/virtual/server/'

    async with Client(url=url) as client:

        uri = 'http://examples.freeopcua.github.io'
        idx = await client.get_namespace_index(uri)

        sensor_value = await client.nodes.root.get_child(["0:Objects", f"{idx}:Component", f"{idx}:SensorValue"])
        command_id = await client.nodes.root.get_child(["0:Objects", f"{idx}:Component", f"{idx}:CommandID"])
        
        while True:
            await asyncio.sleep(update_period_s)
            #write sensor value to virtual device
            await sensor_value.write_value(shared.sensor_value)
            new_sensor_value = await sensor_value.read_value()
            print("[Mirror_Client2] Write to virtual ", sensor_value, new_sensor_value)
            #read command id from virtual device
            shared.command_id = await command_id.read_value()
            print("[Mirror_Client2] Read from virtual ", command_id, shared.command_id)

#start all tasks
if __name__ == '__main__':
    asyncio.run(main())
    #await main()

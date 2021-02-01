# Public OPC UA Mirror Demo

Demo code how to share data from a local OPC UA server to the public without allowing incomming connections in the firewall by using an internal and an external mirror server

# Background

The simplest solution to share data with external institutions is to open the ports of the associated servers in the firewall for incoming connections. However, this poses a significant security risk, as it is very costly to intercept all unauthorized access behind the open firewall.
![Direct Data Exchange](docs/network_scheme_direct.PNG)

It is therefore better if the institutions connect to a shared, public server where only the relevant data is stored. While security is served by this, there is an additional effort for developers, since external data is accessed via a different protocol (e.g. SQL, Websockets, etc.) than internal device data (e.g. REST, OPC UA, etc.).
![Man-in-the-Middle](docs/network_scheme_man-in-the-middle.PNG)

To compensate for this disadvantage as well, virtual OPC UA devices can be made available on a public server of the respective other institution, as demonstrated in this project. These virtual devices behave exactly like the real devices, except that no real hardware is present. Instead, incoming and outgoing data is synchronized between the virtual and the real device via internal and authorized synchronization servers.
![Virtual OPC UA Devices](docs/network_scheme_virtual-opc-ua-server.PNG)



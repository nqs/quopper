'''import bluetooth
 
serverMACAddress = '68:86:E7:02:25:53'
port = 1
s = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
s.connect((serverMACAddress, port))
while 1:
	text ="FFhFEh00h22h00006h000000000"
	if text == "quit":
		break
	s.send(text)
sock.close()

# FFh FEh 00h 22h 000 06h 000 000 000'''

# d: rfcomm-client.py 424 2006-08-24 03:35:54Z albert $

import bluetooth

def whats_nearby():
    name_by_addr = {}
    nearby = bluetooth.discover_devices(flush_cache=True)
    for bd_addr in nearby:
        name = bluetooth.lookup_name( bd_addr, 5)
        print bd_addr, name
        name_by_addr[bd_addr] = name
    return name_by_addr

def what_services( addr, name ):
    print " %s - %s" % ( addr, name )
    for services in bluetooth.find_service(address = addr): 
        print "\t Name:           %s" % (services["name"]) 
        print "\t Description:    %s" % (services["description"]) 
        print "\t Protocol:       %s" % (services["protocol"]) 
        print "\t Provider:       %s" % (services["provider"]) 
        print "\t Port:           %s" % (services["port"]) 
        print "\t service-classes %s" % (services["service-classes"])
        print "\t profiles        %s" % (services["profiles"])
        print "\t Service id:  %s" % (services["service-id"]) 
        print "" 

what_services('68:86:E7:02:25:53', 'sphero')

'''if __name__ == "__main__":
    name_by_addr = whats_nearby()
    for addr in name_by_addr.keys():
        what_services(addr, name_by_addr[addr])'''
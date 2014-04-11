
import bluetooth
nearby_devices = bluetooth.discover_devices(lookup_names = True)

for bdaddr in nearby_devices:
	print bdaddr
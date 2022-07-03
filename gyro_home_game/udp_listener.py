import socket
import time
import json

UDP_IP = "192.168.100.179"
UDP_PORT = 5000

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))


STARTING_POS = {}
Z_CIRCLE_HALF = {}
LAST_CHANGE = {}

last_save = 0

while True:
    current_ms = time.time_ns() // 1000000 % 10000000
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    ip = addr[0]
    x, y, z = [int(float(_part) * 180) + 180 for _part in data.decode('utf8').strip().split(',')]
    if ip not in STARTING_POS:
        STARTING_POS[ip] = (x, y, z)
        Z_CIRCLE_HALF[ip] = (z + 180) % 360
        LAST_CHANGE[ip] = {'x': x, 'y': y, 'z': z, 'ms': current_ms}

    # Detect enough values changed
    x_delta = abs(x - LAST_CHANGE[ip]['x'])
    y_delta = abs(y - LAST_CHANGE[ip]['y'])
    z_delta = abs(z - LAST_CHANGE[ip]['z'])
    if x_delta > 4 or y_delta > 4 or z_delta > 4:
        LAST_CHANGE[ip] = {'x': x, 'y': y, 'z': z, 'ms': current_ms}
        print("%s - %s: %s" % (current_ms, ip, [x, y, z]))

    if abs(z - (STARTING_POS[ip][2] + 180) % 360) < 30:
        Z_CIRCLE_HALF[ip] = True

    if abs(z - STARTING_POS[ip][2]) < 30:
        if Z_CIRCLE_HALF[ip]:
            print(ip, "full cirlcle")
            Z_CIRCLE_HALF[ip] = False

    if current_ms - last_save > 500:
        with open('values.json', 'w') as f:
            json.dump({
                'LAST_CHANGE': LAST_CHANGE
            }, f)
        last_save = current_ms



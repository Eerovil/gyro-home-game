import socket
import time
import json
import os

UDP_IP = "192.168.100.179"
UDP_PORT = 5001

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
data_folder = 'data'

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(0)


STARTING_POS = {}
Z_CIRCLE_HALF = {}
LAST_CHANGE = {}

last_save = 0
current_ms = 0

while True:
    data, addr = (None, None)
    while True:
        print("reading: {}".format(current_ms - time.time_ns() // 1000000 % 10000000))
        try:
            data, addr = sock.recvfrom(64) # buffer size is 1024 bytes
            print("received: {}".format(data))
        except Exception as e:
            print(e)
            break
    if not data:
        time.sleep(0.1)
        continue

    current_ms = time.time_ns() // 1000000 % 10000000
    ip = addr[0]
    x, y, z = [int(float(_part) * 180) + 180 for _part in data.decode('utf8').strip().split(',')]
    if ip not in STARTING_POS:
        STARTING_POS[ip] = (x, y, z)
        Z_CIRCLE_HALF[ip] = (z + 180) % 360
        LAST_CHANGE[ip] = {
            'x': x, 'y': y, 'z': z,
            'ms': current_ms,
            'ip': ip,
            'laps': 0,
        }

    # Detect enough values changed
    x_delta = abs(x - LAST_CHANGE[ip]['x'])
    y_delta = abs(y - LAST_CHANGE[ip]['y'])
    z_delta = abs(z - LAST_CHANGE[ip]['z'])
    if x_delta > 4 or y_delta > 4 or z_delta > 4:
        LAST_CHANGE[ip] = {
            'x': x, 'y': y, 'z': z,
            'ms': current_ms,
            'ip': ip,
            'laps': LAST_CHANGE[ip].get('laps', 0),
        }
        print("%s - %s: %s" % (current_ms, ip, [x, y, z]))

        if current_ms - last_save > 200:
            with open(os.path.join(FILE_PATH, '../data/values.json'), 'w') as f:
                json.dump({
                    'LAST_CHANGE': LAST_CHANGE,
                    'current_ms': current_ms,
                }, f)
            last_save = current_ms


    if abs(z - (STARTING_POS[ip][2] + 180) % 360) < 30:
        Z_CIRCLE_HALF[ip] = True

    if abs(z - STARTING_POS[ip][2]) < 30:
        if Z_CIRCLE_HALF[ip]:
            print(ip, "full cirlcle")
            Z_CIRCLE_HALF[ip] = False
            LAST_CHANGE[ip]['laps'] += 1


    end_ms = time.time_ns() // 1000000 % 10000000
    print("%s: loop took %s" % (current_ms, end_ms - current_ms))

    time.sleep(0.100)

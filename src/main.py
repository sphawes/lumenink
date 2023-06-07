import cv2
import numpy as np
import serial
import sys
import glob

safeZ = 10
drawZ = 7

def scanPorts():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.usb*')
    else:
        print("unknown os")

    valid_ports = []

    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            valid_ports.append(port)
        except (OSError, serial.SerialException):
            pass

    return valid_ports


# # Function to convert lines to array format
# def lines_to_array(lines):
#     lines_array = []
#     for line in lines:
#         x1, y1, x2, y2 = line[0]
#         lines_array.append([(x1, y1), (x2, y2)])
#     return lines_array

cap = cv2.VideoCapture(0)
ports = scanPorts()
ser = serial.Serial(ports[0], 115200, timeout=1)

while True:
    # Capture an image from the camera
    
    ret, frame = cap.read()
    cv2.imshow("live", frame)

    if cv2.waitKey(1) & 0xFF == ord('c'):
        # # Apply Canny edge detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        cv2.drawContours(frame, contours, -1, (0, 255, 0), -1) #---set the last parameter to -1

        cv2.imshow("res",frame)

        line_list = []

        for contour in contours:
            line = []
            for coordinate in contour:
                line.append(coordinate[0])
            line_list.append(line)

        print(line_list)

        # generate gcode

        f = open('draw.gcode', 'w')
        f.truncate()
        f.close
        f = open('draw.gcode', 'a')

        # add any starting gcode
        f.write("G28\n")

        for line in line_list:
            # move head up before going to the correct starting location
            f.write("G0 Z" + str(safeZ) + "\n")

            # go to first position
            f.write("G0 X" + str(line[0][0]) + " Y" + str(line[0][1]) + "\n")

            # move down
            f.write("G0 Z" + str(drawZ) + "\n")

            # do all the rest of the path commands
            for point in line:
                f.write("G0 X" + str(point[0]) + " Y" + str(point[1]) + "\n")
        f.close()

        # now, draw that shit

        f = open('draw.gcode', 'r')
        commands = f.readlines()
        for command in commands:
            encoded = command.encode('utf-8')
            ser.write(encoded + b'\n')
            resp = ser.readline().decode('utf-8')
            print(str(resp))

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and destroy any open windows
cap.release()
cv2.destroyAllWindows()
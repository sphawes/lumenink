import cv2
import numpy as np
#import serial
import sys
import glob
import time
import keyboard

safeZ = 10
drawZ = 7

# def scanPorts():
#     if sys.platform.startswith('win'):
#         ports = ['COM%s' % (i + 1) for i in range(256)]
#     elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
#         # this excludes your current terminal "/dev/tty"
#         ports = glob.glob('/dev/tty[A-Za-z]*')
#     elif sys.platform.startswith('darwin'):
#         ports = glob.glob('/dev/tty.usb*')
#     else:
#         print("unknown os")

#     valid_ports = []

#     for port in ports:
#         try:
#             s = serial.Serial(port)
#             s.close()
#             valid_ports.append(port)
#         except (OSError, serial.SerialException):
#             pass

#     return valid_ports


# # Function to convert lines to array format
# def lines_to_array(lines):
#     lines_array = []
#     for line in lines:
#         x1, y1, x2, y2 = line[0]
#         lines_array.append([(x1, y1), (x2, y2)])
#     return lines_array

cap = cv2.VideoCapture(0)

# ports = scanPorts()
# ser = serial.Serial(ports[0], 115200, timeout=1)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
kernel = np.ones((3,3),np.uint8)

while True:
    
    # Capture an image from the camera
    ret, frame = cap.read()

    # greyscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    #detect faces in image
    faces_rect = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=9)

    # get dimensions of image
    frame_height = frame.shape[0]

    image = None
    height = 0
    width = 0

    y_pos_buffer = 50
    y_neg_buffer = 150

    if len(faces_rect) > 0:
        # set bounds variables
        min_x = 1000000
        max_x = 0
        min_y = 1000000
        max_y = 0
        # finding max boundaries of all faces
        for (x, y, w, h) in faces_rect:
            # if the x min bounds of the face is the smallest x value so far
            if x < min_x:
                # update smallest x
                min_x = x

            if (x+w) > max_x:
                max_x = x+w

            if y < min_y:
                if y > y_neg_buffer:
                    min_y = y - y_neg_buffer
                else:
                    min_y = 0

            if (y+h+y_pos_buffer) > max_y:
                if y+h+y_pos_buffer > frame_height:
                    max_y = frame_height
                else:
                    max_y = y+h+y_pos_buffer

        image = frame[min_y:max_y, min_x:max_x]
        height = max_y - min_y
        width = max_x - min_x
    
    else:
        image = frame
        height = frame.shape[0]
        width = frame.shape[1]

    # now we have the image with appropriate AOI, now we can do line detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    th3 = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,21,5)
    # opening = cv2.morphologyEx(th3, cv2.MORPH_OPEN, kernel)
    # edges = cv2.Canny(th3, 10, 70, apertureSize=3, L2gradient = True)
    cv2.imshow("thresh", th3)
    #cv2.imshow("opening", opening)
    #cv2.imshow("canny",edges)

    # trigger when we press "d"
    if cv2.waitKey(1) == 100:

        print("starting gcode generation and drawing sequence")

        # print "Drawing" on the image
        thickness = 2
        drawing = th3.copy()
        drawing = cv2.rectangle(drawing, (38, 0), (460, 70), (255), -1)
        drawing = cv2.putText(drawing, 'Drawing Now', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0), thickness, cv2.LINE_AA)
        # cv2.startWindowThread()
        # cv2.namedWindow("Drawing Now", cv2.WINDOW_AUTOSIZE)
        cv2.imshow("Drawing Now", drawing)
        time.sleep(0.2)
        cv2.waitKey(1)
        
        contours, hierarchy = cv2.findContours(th3, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # for contour in contours:
        #     if cv2.arcLength(contour,True) > 20:            
        #         cv2.drawContours(frame, contour, -1, (0, 255, 0), 3)

        # cv2.drawContours(image, contours, -1, (0, 255, 0), 1) #---set the last parameter to -1

        # cv2.imshow("res",image)

        line_list = []

        for contour in contours:
            line = []
            for coordinate in contour:
                line.append(coordinate[0])
            line_list.append(line)

        # print(line_list[0])

#  GENERATE
        if(True):
            # generate gcode
            print("opening file and generating gcode")

            # transform variables for setting bottom left position of paper
            x_transform = 200
            y_transform = 100

            paper_width = 100
            paper_height = 150

            # calculate scale required to fix in X
            x_scale = paper_width / width

            # calculate scale required to fit in Y
            y_scale = paper_height / height
            
            scale = x_scale

            if y_scale < x_scale:
                scale = y_scale

            #calculate transform variables

            f = open('draw.gcode', 'w')
            f.truncate()
            f.close
            f = open('draw.gcode', 'a')

            # add any starting gcode
            f.write("G28\n")

            for line in line_list:
                # move head up before going to the correct starting location
                f.write("G0 Z" + str(safeZ) + "\n")

                # print("original x: " + str(line[0][0]))
                # print("new X: " + str((scale*line[0][0])+x_transform))

                # go to first position
                f.write("G0 X" + str((scale*line[0][0])+x_transform) + " Y" + str((scale*(height - line[0][1])) + y_transform) + "\n")

                # move down
                f.write("G0 Z" + str(drawZ) + "\n")

                # do all the rest of the path commands
                for point in line:
                    f.write("G0 X" + str((scale*point[0])+x_transform) + " Y" + str((scale*(height - point[1])) + y_transform) + "\n")
            f.close()

            print("done writing gcode to file")

        time.sleep(1)
#   DRAW
        if(False):
            f = open('draw.gcode', 'r')
            commands = f.readlines()
            for command in commands:
                encoded = command.encode('utf-8')
                ser.write(encoded + b'\n')
                resp = ser.readline().decode('utf-8')
                print(str(resp))

        
        cv2.destroyAllWindows()

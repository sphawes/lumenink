import cv2
import numpy as np
import serial
import sys
import glob
import time
import keyboard
import screeninfo

safeZ = 23
drawZ = 7

cap = cv2.VideoCapture(0)

# ports = scanPorts()
# ser = serial.Serial(ports[0], 115200, timeout=1)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
kernel = np.ones((3,3),np.uint8)

# get the size of the screen
screen = screeninfo.get_monitors()[0]
screen_width, screen_height = screen.width, screen.height

# checks for valid serial ports and opens ser object to the first one found
ports = glob.glob('/dev/ttyACM*')
for port in ports:
    try:
        ser = serial.Serial(port, timeout=100)
        ser.close()
        break
    except (OSError, serial.SerialException):
        pass

if ser == None:
    print("no valid serial port found")
    sys.exit()

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

    y_pos_buffer = 15
    y_neg_buffer = 45

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

    window_name = 'live'
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.moveWindow(window_name, screen.x - 1, screen.y + 5)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow(window_name, th3)

    # trigger when we press "d"
    if cv2.waitKey(1) == 100:

        print("starting gcode generation and drawing sequence")

        # print "Drawing" on the image
        path = r'src/drawing.png'
        drawing = cv2.imread(path)

        window_name = 'Drawing Now'
        cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
        cv2.moveWindow(window_name, screen.x - 1, screen.y + 5)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        cv2.imshow(window_name, drawing)
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
            x_transform = 298
            y_transform = 200

            paper_width = 90
            paper_height = 125

            # calculate scale required to fix in X
            x_scale = paper_width / width

            # calculate scale required to fit in Y
            y_scale = paper_height / height

            scale = None
            x_transform_center = 0
            y_transform_center = 0
            
            # if image is taller than the paper's aspect ratio
            if y_scale < x_scale:
                # we need an X offset to center, so find the width of the image after scaled at y scale
                scale = y_scale
                scaled_width = scale * width
                x_transform_center = (paper_width - scaled_width) / 2


            # if image is wider than the paper's aspect ratio
            else:
                # we need a Y offset to center, so find the height of the image after scaled at x scale
                scale = x_scale
                scaled_height = scale * height
                y_transform_center = (paper_height - scaled_height) / 2

            #calculate transform variables

            f = open('draw.gcode', 'w')
            f.truncate()
            f.close
            f = open('draw.gcode', 'a')

            # add any starting gcode
            f.write("G28\n")
            f.write("G0 F10000\n")

            for line in line_list:
                # move head up before going to the correct starting location
                f.write("G0 Z" + str(safeZ) + "\n")

                # go to first position
                f.write("G0 X" + str((scale*line[0][0]) + x_transform + x_transform_center) + " Y" + str((scale*(height - line[0][1])) + y_transform + y_transform_center) + "\n")

                # move down
                f.write("G0 Z" + str(drawZ) + "\n")

                # do all the rest of the path commands
                firstPoint = True
                for point in line:
                    # if it's the first point, skip and set the flag because we're already there
                    if firstPoint:
                        firstPoint = False

                    # write all the rest of the points in the line object
                    else:
                        f.write("G0 X" + str((scale*point[0])+x_transform + x_transform_center) + " Y" + str((scale*(height - point[1])) + y_transform + y_transform_center) + "\n")

                # finally, go back to the first position again to close the loop
                f.write("G0 X" + str((scale*line[0][0])+x_transform + x_transform_center) + " Y" + str((scale*(height - line[0][1])) + y_transform + y_transform_center) + "\n")
            
            # Write ending Gcode
            f.write("G0 Z31.5\n")
            
            f.close()

            print("done writing gcode to file")

#   DRAW IMAGE
        if(True):
            ser.open()
            f = open('draw.gcode', 'r')
            commands = f.readlines()
            for command in commands:
                encoded = command.encode('utf-8')
                ser.write(encoded + b'\n')
                resp = ser.readline().decode('ISO-8859-1')
                print(str(resp))
            ser.close()

#   DRAW LOGO
        if(True):
            ser.open()
            f = open('opulo.gcode', 'r')
            commands = f.readlines()
            for command in commands:
                encoded = command.encode('utf-8')
                ser.write(encoded + b'\n')
                resp = ser.readline().decode('ISO-8859-1')
                print(str(resp))
            ser.close()


        cv2.destroyAllWindows()

    if cv2.waitKey(1) == 101:
        cv2.destroyAllWindows()
        break

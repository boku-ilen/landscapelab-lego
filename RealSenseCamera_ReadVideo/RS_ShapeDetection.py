# Used pyrealsense2 on License: Apache 2.0.

# TODO: optimization possibilities:
# temporal filtering (IIR filter) to remove "holes" (depth=0), hole-filling
# edge-preserving filtering to smooth the depth noise
# changing the depth step-size
# IR pattern removal

import pyrealsense2 as rs
import imutils
import numpy as np
import cv2
import colorsys

# For resolution 1280x720 and distance ~1 meter a short side of lego piece has ~14 px length
WIDTH = int(1280)
HEIGHT = int(720)
# Side of lego piece
MIN_LENGTH = 4
MAX_LENGTH = 35
# Objects in greater distance to the board than (1 +- CLIP) * x will be excluded from processing
CLIP = 0.04
# Aspect ratio for square and rectangle
MIN_SQ = 0.7
MAX_SQ = 1.3
MIN_REC = 0.2
MAX_REC = 2.5
# accepted HSV colors
BLUE_MIN = (0.53, 0.33, 141)
BLUE_MAX = (0.65, 1, 255)
RED_MIN = (0.92, 0.33, 170)
RED_MAX = (1, 1, 255)


# Check if the shape is the searched object
def detect(contour):
    # Initialize the shape name and approximate the contour with Douglas-Peucker algorithm
    shape = "shape"
    epsilon = 0.1 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)

    # Check if the shape has 4 vertices
    if len(approx) == 4:
        # Compute the rotated bounding box and draw all found objects (red)
        # For testing purposes, later should be computed only in the loop and without drawing
        rect = cv2.minAreaRect(c)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        cv2.drawContours(frame, [box], 0, (0, 0, 255), 2)

        # Compute the bounding box of the contour and the aspect ratio
        (x, y, w, h) = cv2.boundingRect(approx)

        # Check the size and color of the shape to decide if it is the searched object
        if (MIN_LENGTH < h < MAX_LENGTH) & (MIN_LENGTH < w < MAX_LENGTH):
            shape = check_if_square(box)
    return shape


# Check if square or rectangle
def check_if_square(box):
    sides_length = calculate_size(box)
    # Compute the aspect ratio
    ar = int(sides_length[0]) / int(sides_length[1])
    shape = "shape"
    print("_________")
    if MIN_SQ <= ar <= MAX_SQ:
        shape = "square"
        print("Square size:", sides_length[0], sides_length[1])
    elif MIN_REC < ar < MAX_REC:
        shape = "rectangle"
        print("Rectangle size:", sides_length[0], sides_length[1])
    return shape


# Calculate two sides from one of corners
def calculate_size(box):
    length = []
    for idx in range(3):
        length.append(np.linalg.norm(box[0] - box[idx+1]))
    # Delete the highest value (diagonal), only two sides lengths are remaining in the array
    return np.delete(length, np.argmax(length))


# TODO: find correct RGB
def check_color(x, y):
    # calculate the mean color (RGB)
    color = cv2.mean(color_image[y:y+4, x:x+4])
    # print("RGB:", color[2], color[1], color[0])

    colorHSV = colorsys.rgb_to_hsv(color[2], color[1], color[0])
    print("HSV:", colorHSV)

    if (RED_MIN <= colorHSV <= RED_MAX) | (BLUE_MIN <= colorHSV <= BLUE_MAX):
        return True
    return False


# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, WIDTH, HEIGHT, rs.format.z16, 30)
config.enable_stream(rs.stream.color, WIDTH, HEIGHT, rs.format.bgr8, 30)

middleX = int(WIDTH/2)
middleY = int(HEIGHT/2)
# Initialize the clipping distance
clip_dist = 0

# Create alignment primitive with color as its target stream:
align = rs.align(rs.stream.color)

# Start streaming
profile = pipeline.start(config)

# Getting the depth sensor's depth scale
depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
print("Depth Scale is: ", depth_scale)

try:
    while True:
        # Wait for depth and color frames
        frames = pipeline.wait_for_frames()
        # Align the depth frame to color frame
        aligned_frames = align.process(frames)
        # Get aligned frames
        aligned_depth_frame = aligned_frames.get_depth_frame()  # aligned_depth_frame is a 640x480 depth image
        color_frame = aligned_frames.get_color_frame()

        # Validate that both frames are valid
        if not aligned_depth_frame or not color_frame:
            continue

        # Convert images to numpy arrays
        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        # Get the distance to the board (the middle of the frame)
        if clip_dist == 0:
            clip_dist = aligned_depth_frame.get_distance(middleX, middleY) / depth_scale
            print("Distance to the table is:", clip_dist)

        # Change background regarding clip_dist to black (depth image is 1 channel, color is 3 channels)
        depth_image_3d = np.dstack((depth_image, depth_image, depth_image))
        bg_removed = np.where((depth_image_3d > clip_dist * (1 + CLIP)) | (depth_image_3d < clip_dist * (1 - CLIP)), 0, color_image)

        # Render aligned images
        # depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
        # images = np.hstack((bg_removed, depth_colormap))
        cv2.namedWindow('Aligned', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('Aligned', bg_removed)

        # Change the white board to black and find objects

        # TODO: to optimize find the whiteboard and crop to it
        # TODO: maybe not needed if clipping with depth information used
        # crop_frame = bg_removed[50:120, 435:600]

        frame = bg_removed

        # Convert the image to grayscale
        img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Change whiteboard to black (contours are to find from black background)
        thresh = cv2.threshold(img_gray, 140, 255, cv2.THRESH_BINARY)[1]
        frame[thresh == 255] = 0
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        erosion = cv2.erode(frame, kernel, iterations=1)

        # TODO: check if it helps
        # Trying to remove gray colors to ignore shadows
        frame_HSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        thresh = cv2.inRange(frame_HSV, (0, 0, 0), (255, 255, 120))
        frame[thresh == 255] = 0

        # Convert the resized image to grayscale, blur it slightly, and threshold it
        img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(img_gray, (5, 5), 0)
        thresh = cv2.threshold(blurred, 55, 255, cv2.THRESH_BINARY)[1]

        # Find contours in the thresholded image
        contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0] if imutils.is_cv2() else contours[1]

        # Loop over the contours
        for c in contours:
            # compute the center of the contour (cX, cY) and detect whether it is the searched object
            M = cv2.moments(c)
            if M["m00"] != 0:
                cX = int((M["m10"] / M["m00"]))
                cY = int((M["m01"] / M["m00"]))
                shape = detect(c)
                if shape != "shape":
                    check = False
                    # Check color (currently only red and blue accepted)
                    check = check_color(cX, cY)
                    print("Coordinates:", cX, cY, check)
                    if check:
                        cv2.drawContours(frame, [c], -1, (0, 255, 0), 3)
                        cv2.putText(frame, shape, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # Render shape detection images
        cv2.namedWindow('Shape detection', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('Shape detection', frame)
        cv2.waitKey(1)

finally:

    # Stop streaming
    pipeline.stop()

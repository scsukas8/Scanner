# This program is intended to be used for scanning single sheets of paper.
# The program should enable the webcam, find a four pointed polygon, apply
# the perpective transform, and save the image.

# import the necessary packages
from transform import four_point_transform
from util import *
import numpy as np
import cv2
import os
 
DEBUG = False
SHOW_OUTLINE = False

def scan(num_attempts = 1):
    # Expected width to height ratio of the scan (Width/Height)
    scan_aspect_ratio = 8.5 / 11

    # Aspect ratio margin of error
    epsilon = .25

    # The minimum size of the scan relative to the capture.
    minSize = 0.20

    # Finished scan will be stored in 'scan'
    scan = None
    screenCnt = None


    # Make 5 attempts to capture the image

    for attempt in xrange(num_attempts):

        # Pull in frame from webcam
        retval, frame = grab_from_file()
        if not retval:
            continue


        # load the image and compute the ratio of the old height
        # to the new height, clone it, and resize it
        # Reducing the image size speeds processing
        HEIGHT = 500.0
        image = frame.copy()
        ratio = image.shape[0] / HEIGHT
        orig = image.copy()
        image = cv2.resize(orig,(int(image.shape[1]/ratio),int(HEIGHT)))
        origResize = image.copy()

        # convert the image to grayscale, blur it, and find edges
        # in the image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        otsu, _ = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        edged = cv2.Canny(image,otsu, otsu * 2)

        if DEBUG:
            # show the original image and the edge detected image
            print "STEP 1: Edge Detection"
            cv2.imshow("Image", image)
            cv2.imshow("Edged", edged)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        # find the contours in the edged image, keeping only the
        # largest ones, and initialize the screen contour
        (cnts, _) = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:5]


        # loop over the contours
        for cnt in cnts:
            # approximate the contour
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            cv2.drawContours(image, [approx], -1, (0, 255, 0), 2)
            # if our approximated contour has four points, then we
            # can assume that we have found our screen
            if len(approx) == 4:
                screenCnt = approx
                break

        # If a capture not found, screenCnt will be None,
        # and the process will be restarted
        if not screenCnt is None:
            cv2.drawContours(image, [screenCnt], -1, (0, 255, 0), 2)
        else:
            print "No capture found"
            continue


        # apply the four point transform to obtain a top-down
        # view of the original image
        warped = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)


         
         
        if DEBUG:
            # show the original and scanned images
            print "STEP 3: Apply perspective transform"
            cv2.imshow("Original", origResize)
            cv2.imshow("Scanned", warped)
            cv2.waitKey(0)

        # By looking at the dimensions of the flattened image,
        # the image can be validated to see it is a valid capture
        warped_height, warped_width, _ = warped.shape
        warped_ratio = warped_width/float(warped_height)
        
        # If scan is landscape, transpose Width&Height
        if (scan_aspect_ratio < 1 and warped_ratio > 1) or \
           (scan_aspect_ratio > 1 and warped_ratio < 1):
           warped_height, warped_width = warped_width, warped_height
           warped_ratio = warped_width/float(warped_height)


        # Check to see if the capture is within some margin
        # of the expect aspect ratio.
        if abs(warped_ratio - scan_aspect_ratio) > epsilon:
            continue
        # Check to see if the image is at least some size
        # relative to the full size of the frame
        elif abs(warped_height / float(image.shape[0])) < minSize:
            continue


        print "Capture found!"

        # Reshape the scan to match the expected size
        scan = warped.copy()
        scan_height = warped_height
        scan_width = (int) (warped_height * scan_aspect_ratio)
        scan = cv2.resize(scan, (scan_height,scan_width))
        return scan



def save_scan(scan):
    # Save image
    save_dir = "\saved_scans\Scan.jpg"
    path = os.getcwd() + save_dir
    cv2.imwrite(path, scan)
    return path

def open_scan(path):
    # Open image in default program
    os.system("\""+ path + "\"")



scan = scan()
path = save_scan(scan)
open_scan(path)
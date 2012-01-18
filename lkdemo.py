#! /usr/bin/env python

print "OpenCV Python version of lkdemo"

import sys

# import the necessary things for OpenCV
from cv2 import cv


from Xlib import X, display

#############################################################################
# some "constants"

win_size = 10
MAX_COUNT = 500

#############################################################################
# some "global" variables

image = None
pt = None
add_remove_pt = False
flags = 0
night_mode = False
need_to_init = False
# the default parameters
quality = 0.01
min_distance = 10

#############################################################################
# the mouse callback

# the callback on the trackbar
def on_mouse (event, x, y, flags, param):

    # we will use the global pt and add_remove_pt
    global pt
    global add_remove_pt
    
    if image is None:
        # not initialized, so skip
        return

    if event == cv.CV_EVENT_LBUTTONDOWN:
        # user has click, so memorize it
        pt = (x, y)
        add_remove_pt = True

#############################################################################
# so, here is the main part of the program

if __name__ == '__main__':

    try:
        # try to get the device number from the command line
        device = int (sys.argv [1])

        # got it ! so remove it from the arguments
        del sys.argv [1]
    except (IndexError, ValueError):
        # no device number on the command line, assume we want the 1st device
        device = 0

    if len (sys.argv) == 1:
        # no argument on the command line, try to use the camera
        capture = cv.CreateCameraCapture (device)

    else:
        # we have an argument on the command line,
        # we can assume this is a file name, so open it
        capture = cv.CreateFileCapture (sys.argv [1])            

    # check that capture device is OK
    if not capture:
        print "Error opening capture device"
        sys.exit (1)
        
    # display a small howto use it
    print "Hot keys: \n" \
          "\tESC - quit the program\n" \
          "\tr - auto-initialize tracking\n" \
          "\tc - delete all the points\n" \
          "\tn - switch the \"night\" mode on/off\n" \
          "To add/remove a feature point click it\n"

    # first, create the necessary windows
    cv.NamedWindow ('LkDemo', cv.CV_WINDOW_AUTOSIZE)

    # register the mouse callback
    cv.SetMouseCallback ('LkDemo', on_mouse, None)

    while 1:
        # do forever

        # 1. capture the current image
        frame = cv.QueryFrame (capture)
        if frame is None:
            # no image captured... end the processing
            break

        if image is None:
            # create the images we need
            image = cv.CreateImage (cv.GetSize (frame), 8, 3)
            grey = cv.CreateImage (cv.GetSize (frame), 8, 1)
            prev_grey = cv.CreateImage (cv.GetSize (frame), 8, 1)
            pyramid = cv.CreateImage (cv.GetSize (frame), 8, 1)
            prev_pyramid = cv.CreateImage (cv.GetSize (frame), 8, 1)
            eig = cv.CreateImage (cv.GetSize (frame), cv.IPL_DEPTH_32F, 1)
            temp = cv.CreateImage (cv.GetSize (frame), cv.IPL_DEPTH_32F, 1)
            points = [[], []]

        # copy the frame, so we can draw on it
        cv.Copy (frame, image)



        cv.Flip(image, None, 1)


        # create a grey version of the image
        cv.CvtColor (image, grey, cv.CV_BGR2GRAY)

        if night_mode:
            # night mode: only display the points
            cv.SetZero (image)

        if need_to_init:
            # we want to search all the good points
            # create the wanted images
            
            # search the good points
            points [1] = cv.GoodFeaturesToTrack (
                grey, eig, temp,
                MAX_COUNT,
                quality, min_distance, None, 3, 0, 0.04)
            
            # refine the corner locations
            cv.FindCornerSubPix (
                grey,
                points [1],
                (win_size, win_size) (-1, -1),
                (cv.CV_TERMCRIT_ITER | cv.CV_TERMCRIT_EPS,
                                   20, 0.03))
                                               
        elif len (points [0]) > 0:
            # we have points, so display them

            # calculate the optical flow
            [points [1], status], something = cv.CalcOpticalFlowPyrLK (
                prev_grey, grey, prev_pyramid, pyramid,
                points [0], len (points [0]),
                (win_size, win_size), 3,
                len (points [0]),
                None,
                (cv.CV_TERMCRIT_ITER|cv.CV_TERMCRIT_EPS,
                                   20, 0.03),flags)

            # initializations
            point_counter = -1
            new_points = []

            for the_point in points [1]:
                # go trough all the points

                # increment the counter
                point_counter += 1

                if add_remove_pt:
                    # we have a point to add, so see if it is close to
                    # another one. If yes, don't use it
                    dx = pt.x - the_point.x
                    dy = pt.y - the_point.y
                    if dx * dx + dy * dy <= 25:
                        # too close
                        add_remove_pt = 0
                        continue

                if not status [point_counter]:
                    # we will disable this point
                    continue

                # this point is a correct point
                new_points.append (the_point)

                # draw the current point
                cv.Circle (image,
                             cv.PointFrom32f(the_point),
                             3, cv.Scalar (0, 255, 0, 0),
                             -1, 8, 0)

            # set back the points we keep
            points [1] = new_points
            
        if add_remove_pt:
            # we want to add a point
            points [1].append (pt)

            # refine the corner locations
            points [1][-1] = cv.FindCornerSubPix (
                grey,
                [points [1][-1]],
                (win_size, win_size), (-1, -1),
                (cv.CV_TERMCRIT_ITER | cv.CV_TERMCRIT_EPS,
                                   20, 0.03))[0]

            # we are no more in "add_remove_pt" mode
            add_remove_pt = False

        # swapping
        prev_grey, grey = grey, prev_grey
        prev_pyramid, pyramid = pyramid, prev_pyramid
        points [0], points [1] = points [1], points [0]

        try:
            d = display.Display()
            s = d.screen()
            root = s.root

            root.warp_pointer(((points[0][0].x - 220) * 4080 / 200), ((points[0][0].y - 220) * 1920 / 200))

            d.sync()

        except:
            pass


        need_to_init = False
        
        # we can now display the image
        cv.ShowImage ('LkDemo', image)

        # handle events
        c = cv.WaitKey (10)

        if c == '\x1b':
            # user has press the ESC key, so exit
            break

        # processing depending on the character
        if c in ['r', 'R']:
            need_to_init = True
        elif c in ['c', 'C']:
            points = [[], []]
        elif c in ['n', 'N']:
            night_mode = not night_mode

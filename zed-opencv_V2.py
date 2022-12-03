import sys
import numpy as np
import math
import pyzed.sl as sl
import cv2
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject


def main() :

    # Create a ZED camera object
    zed = sl.Camera()

    # Set configuration parameters
    input_type = sl.InputType()
    if len(sys.argv) >= 2 :
        input_type.set_from_svo_file(sys.argv[1])
    init = sl.InitParameters(input_t=input_type)
    init.camera_resolution = sl.RESOLUTION.HD1080
    init.depth_mode = sl.DEPTH_MODE.ULTRA
    init.coordinate_units = sl.UNIT.METER

    # Open the camera
    err = zed.open(init)
    if err != sl.ERROR_CODE.SUCCESS :
        print(repr(err))
        zed.close()
        exit(1)

  
    # Set runtime parameters after opening the camera
    runtime = sl.RuntimeParameters()
    runtime.sensing_mode = sl.SENSING_MODE.FILL
    
    # Setting the depth confidence parameters
    runtime.confidence_threshold = 100
    runtime.textureness_confidence_threshold = 100

    # Prepare new image size to retrieve half-resolution images
    image_size = zed.get_camera_information().camera_resolution
    image_size.width = image_size.width /2
    image_size.height = image_size.height /2
    
    image_size_out = zed.get_camera_information().camera_resolution
    image_size_out.width = image_size.width 
    image_size_out.height = image_size.height 
    
    # Declare your sl.Mat matrices
    image_zed = sl.Mat(image_size.width, image_size.height)
    # Declare your sl.Mat matrices for out_send
    image_zed_out = sl.Mat(image_size_out.width, image_size_out.height, sl.MAT_TYPE.U8_C4)
    depth_image_zed = sl.Mat(image_size.width, image_size.height, sl.MAT_TYPE.U8_C4)
    point_cloud = sl.Mat()
   
                             
    out_send = cv2.VideoWriter('appsrc ! videoconvert ! videoscale ! video/x-raw,format=YUY2,width=1280,height=720,framerate=30/1 ! nvvidconv ! \
                            nvv4l2h264enc bitrate=12000000 insert-sps-pps=1 ! video/x-h264, \
                            stream-format=byte-stream ! rtph264pay pt=96 ! \
                            udpsink host=127.0.0.1 port=5400 async=false',
                            cv2.CAP_GSTREAMER, 0, 30, (1920,1080), True)
                                                                   
    if not out_send.isOpened():
        print('VideoWriter not opened')
        exit(0)
    
    rtsp_port_num = 8554 

    server = GstRtspServer.RTSPServer.new()
    server.props.service = "%d" % rtsp_port_num
    server.attach(None)
    codec="H264"
    updsink_port_num = 5400
    factory = GstRtspServer.RTSPMediaFactory.new()
    factory.set_launch("(udpsrc name=pay0 port=%d buffer-size=524288 caps=\"application/x-rtp, media=video, clock-rate=90000, encoding-name=(string)%s, payload=96 \" )" % (updsink_port_num, codec))
                    
    factory.set_shared(True)
    server.get_mount_points().add_factory("/ds-test", factory)
    
    # output  rtsp info
    print("\n *** Launched RTSP Streaming at rtsp://localhost:%d/ds-test ***\n\n" % rtsp_port_num)    

    key = ' '
    #while key != 113 :
    while True:
        err = zed.grab(runtime)
        def click_event (event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                # Retrieve the left image, depth image in the half-resolution
                zed.retrieve_image(image_zed, sl.VIEW.LEFT, sl.MEM.CPU, image_size)
                zed.retrieve_image(depth_image_zed, sl.VIEW.DEPTH, sl.MEM.CPU, image_size)
                # Retrieve the RGBA point cloud in half resolution
                zed.retrieve_measure(point_cloud, sl.MEASURE.XYZRGBA, sl.MEM.CPU, image_size)
                err, point_cloud_value = point_cloud.get_value(x, y)
                distance = math.sqrt(point_cloud_value[0] * point_cloud_value[0] +
                                     point_cloud_value[1] * point_cloud_value[1] +
                                     point_cloud_value[2] * point_cloud_value[2])
                                                         

                print("Distance to Camera at ({}, {}) (image center): {:1.3} m".format(x, y,  distance))
            
        if err == sl.ERROR_CODE.SUCCESS :
            
            # Retrieve the left image, depth image in the half-resolution
            zed.retrieve_image(image_zed, sl.VIEW.LEFT, sl.MEM.CPU, image_size)
            # Retrieve the left image only
            zed.retrieve_image(image_zed_out, sl.VIEW.LEFT)
            zed.retrieve_image(depth_image_zed, sl.VIEW.DEPTH, sl.MEM.CPU, image_size)
            # Retrieve the RGBA point cloud in half resolution
            zed.retrieve_measure(point_cloud, sl.MEASURE.XYZRGBA, sl.MEM.CPU, image_size)


            # To recover data from sl.Mat to use it with opencv, use the get_data() method
            # It returns a numpy array that can be used as a matrix with opencv
            image_ocv = image_zed.get_data()
            image_ocv_out = image_zed_out.get_data()
            # Convert RGBA to RGB for out_send.write
            image_RGB = cv2.cvtColor(image_ocv_out, cv2.COLOR_RGBA2RGB)
            depth_image_ocv = depth_image_zed.get_data()
            
            cv2.imshow('Image', image_ocv) 
            # out_send in A RTSP stream
            out_send.write(image_RGB)    
            cv2.setMouseCallback('Image', click_event)
            key = cv2.waitKey(10)
           
    
    cv2.destroyAllWindows()
    zed.close()

    print("\nFINISH")

if __name__ == "__main__":
    main()
    
    
    
    
    
    
    
    
    
    
    

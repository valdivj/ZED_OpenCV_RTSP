# ZED_OpenCV_RTSP
 Capture Zed camera stream then use Opencv to maniplulate the depth data and then send stream back out RTSP

I used the Sterolabs Github repo example "zed-opencv" and "tutorial 3 - depth sensing" in the zed-example repo 
to create "zed-opencv_V2.py"

It uses pyhton to open up a ZED stream and lets you click on a pixel of the image stream and returns 
the Pixel corordiantes and the depth reading of that pixel.

Then it sends the captured ZED camera stream back out as a RTSP stream
so it can be played in a VLC player on any computer on network
or the Nvidia Deepstream pipeline.

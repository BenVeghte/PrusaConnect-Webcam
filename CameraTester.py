import cv2
import subprocess
import os
import argparse

def verifyCamera(camera_id:str) -> bool:
    """Test to see if the camera can take a photo. Occasionally a camera will have multiple v4l devices so this makes sure you have selected the right one

    Args:
        camera_id (str): Path to the camera, relative to /dev/v4l/by-id/

    Returns:
        bool: Returns whether the camera is valid or not
    """
    camera_path = "/dev/v4l/by-id/" + camera_id

    cap = cv2.VideoCapture(camera_path)
    if cap.isOpened():
        ret, frame = cap.read()
        cap.release()
        return ret
    else:
        print("Video Capture was unable to be opened, this may be because another camera is actively using it")
        return False

def allCameraSnapshot():
    """Takes a photo with all connected USB V4L cameras (or at least tries to) and saves them so the user can figure out which camera is pointed where
    """
    result = subprocess.run(["ls", "/dev/v4l/by-id/"], stdout=subprocess.PIPE).stdout.decode('utf-8').replace('\n', ' ')
    v4l_devices = result.strip().split(' ')
    for camera_id in v4l_devices:
        camera_path = "/dev/v4l/by-id/" + camera_id
        cap = cv2.VideoCapture(camera_path)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret == True:
                cv2.imwrite(f"{camera_id}.jpg", frame)
                print(camera_id)
            
        cap.release()
    
    print(f"All photos captured to {os.getcwd()}, copy the file name (minus the file extention) to the parameters of prusacam.py")
    
    
if __name__ == "__main__":
    print("Taking a photo from all connected V4L cameras")
    allCameraSnapshot()

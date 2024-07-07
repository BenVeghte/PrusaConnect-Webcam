import cv2
import subprocess
import os
import sys

import json

if sys.platform =="win32": #Conditional imports so as not to bulk up non-windows system
    import winrt.windows.devices.enumeration as windows_devices
    import asyncio
    async def getWinConnDev():
        return await windows_devices.DeviceInformation.find_all_async(4) #Devices classes found here: https://learn.microsoft.com/en-us/uwp/api/windows.devices.enumeration.deviceclass?view=winrt-26100 

    def getWindowsCameras() -> list:
        """Get a list of the windows cameras

        Returns:
            list: [[List of camera names], [List of Camera ids]]
        """
        devs = asyncio.run(getWinConnDev())
        ids = [camera.id for camera in devs]
        names = [camera.name for camera in devs]

        return [names, ids]

    def matchWinCamera(camera_id:str) -> int:
        """Matches the windows camera id, like from getWindowsCameras, to the integer to use with cv2.VideoCapture

        Args:
            camera_id (str): Camera ID, like from getWindowsCameras

        Returns:
            int: integer to use with cv2.VideoCapture
        """
        try:
            ind = getWindowsCameras()[1].index(camera_id)
        except ValueError:
            raise ConnectionError("Unable to match supplied windows camera id to currently connected camera")
        return ind


else:
    def getWindowsCameras() -> None:
        """Place holder function to prevent NameErrors from occuring
        """
        return None
    def matchWinCamera() -> None:
        """Place holder function to prevent NameErrors from occuring
        """
        return None


def verifyCamera(camera_id:str) -> bool:
    """Test to see if the camera can take a photo. Occasionally a camera will have multiple v4l devices so this makes sure you have selected the right one

    Args:
        camera_id (str): Path to the camera, relative to /dev/v4l/by-id/ if on linux or the camera id as obtained from getWindowsCameras

    Returns:
        bool: Returns whether the camera is valid or not
    """
    if sys.platform == "win32":
        try:
            if type(camera_id) is int:
                ind = camera_id
            else:
                ind = getWindowsCameras()[1].index(camera_id)
            cap = cv2.VideoCapture(ind)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                return ret
            
            else:
                return False
            
        except ValueError: #If there is no match for the camera id
            return False

    else:
        camera_path = "/dev/v4l/by-id/" + camera_id

        cap = cv2.VideoCapture(camera_path)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            return ret
        else:
            return False

def allCameraSnapshot():
    """Takes a photo with all connected cameras (or at least tries to) and saves them so the user can figure out which camera is pointed where
    """
    if sys.platform == "win32":
        names, ids = getWindowsCameras()
        if len(names) == 0:
            print("No cameras available, check your connections")
            return
        print("IMAGE -> CAMERA ID")
        for i, id in enumerate(ids):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret == True:
                    cv2.imwrite(f"Camera {i}.jpg", frame)
                    rep_id = id.replace('\\' , '\\\\')
                    print(f"Camera {i}.jpg -> {rep_id}")
            
            cap.release()
        print(f"All photos captured to {os.getcwd()}, copy the CAMERA ID string to the parameters of prusacam.py or JSON file")

    else:
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
    
        print(f"All photos captured to {os.getcwd()}, copy the file name (minus the file extention) to the parameters of prusacam.py or JSON file")
    

if __name__ == "__main__":
    print("Taking a photo from all connected cameras")
    allCameraSnapshot()

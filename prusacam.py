import requests
import argparse
import cv2 
import datetime
import pathlib
from PIL import Image
import json
import time
import json
import os
import logging
import sys
import CameraTester

DEFAULT_MAX_IMAGES = 500
TIMESTAMP_FMT = '%Y-%m-%d_%H_%M_%S'

logger = logging.getLogger("prusacam")
logger.setLevel(logging.DEBUG)



#Can either supply configuration json file
parser = argparse.ArgumentParser(description="Use the arguments to pass the token and camera path to the script, can either use just json or the rest of them")
parser.add_argument("-t", "--token", help="Token created by Prusa Connect")
parser.add_argument("-n", "--name", help="Printer name to assist in debugging", default="printer")
parser.add_argument("-f", "--fingerprint", help="Unique fingerprint >16 characters long")
parser.add_argument("-i", "--ip", help="Local IP address of the printer to check print status")
parser.add_argument("-k", "--apikey", help="PrusaLink API key, found on printer settings page of prusa connect")
parser.add_argument("-d", "--directory", help="Absolute path to directory where to store images")
parser.add_argument("-m", "--maximages", help = "Maximum number of images for this camera to store in image folder", default = DEFAULT_MAX_IMAGES)
parser.add_argument("-j", "--json", help="Absolute file path to configuration json file", default = None)
parser.add_argument("-r", "--rotate", help="How much to rotate the image by, needs to be a multiple of 90, optional", default=0)
parser.add_argument("-c", "--camera", help="Absolute path to the camera", default=None)



def putImage(token:str, fingerprint:str, img_path:pathlib.Path) -> requests.Response|None:
    """Send the image to PrusaConnect

    Args:
        token (str): Camera API Token
        fingerprint (str): The fingerprint set for the camera token (set at the time of the first use of the Camera API Token)
        img_path (pathlib.Path): Absolute path to the photo just taken

    Returns:
        requests.Response: Response from the prusa servers
        None: If the servers cannot be reached, return none
    """
    snapshot_headers = {
        'Content-Type': 'image/jpg',
        'fingerprint': fingerprint,
        'token': token
    }

    URL = "https://connect.prusa3d.com/c/snapshot"

    with img_path.open(mode='rb') as f:
        image = f.read()
    
    try:
        resp = requests.put(url=URL, headers=snapshot_headers, data = image)
        if resp.status_code == 200: #Successful upload of image
            logger.debug(f"{img_path.name} uploaded successfully")
        
        else:
            logger.exception(f"Put Image: Response Code {resp.status_code}. Content: {resp.content.decode()}")
            raise ConnectionError(f"Put Image: Response Code {resp.status_code}. Content: {resp.content.decode()}") 

        return resp
       
    except requests.exceptions.ConnectTimeout:
        logger.warn("Put Image: Connection Timeout. Meaning {URL} could not be accessed")
        return None
    

def getPrinterStatus(ip:str, api_key:str) -> dict:
    """Get the printer status from the PrusaLink webserver, possible statuses can be found here: https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml#L1269

    Args:
        ip (str): IP Address of the printers PrusaLink web interface
        api_key (str): PrusaLink API Key

    Returns:
        dict: Content of the HTTP request response
        None: If the connection times out, returns None instead
    """

    try:
        resp = requests.get(url=f"http://{ip}/api/v1/status", headers = {"x-api-key":api_key})

        #See https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml#L43 for info about status codes and response format
        if resp.status_code == 200:
            return json.loads(resp.content)

        else:
            logger.exception(f"Printer Status: Response Code {resp.status_code}. Content: {resp.content.decode()}")
            raise ConnectionError(f"Printer Status: Response Code {resp.status_code}. Content: {resp.content.decode()}") 

    except requests.exceptions.ConnectTimeout:
        logger.warn(f"Printer status check timeout. IP: {ip}")
        return None


def captureImage(camera_id:int|str, fingerprint:str, imgs_folder:pathlib.Path, rotation:int) -> pathlib.Path:
    """Take a photo with the selected webcam

    Args:
        camera_id (int|str): Integer of the camera as chosen by selectCamera() or the absolute path to the camera
        fingerprint (str): The fingerprint set for the camera token (set at the time of the first use of the Camera API Token)
        imgs_folder (pathlib.Path): Absolute path to the images folder where to save the images taken
        rotation (int): Input to use with cv2.rotate. Possible: None for no rotation, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE, cv2.ROTATE_180

    Returns:
        pathlib.Path: Absolute path to the image just taken
    """

    #Capture image
    cap = cv2.VideoCapture(camera_id)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret == True:
            file_name = f"{fingerprint}_{datetime.datetime.now().strftime(TIMESTAMP_FMT)}.jpg"
            img_path = imgs_folder/file_name

            #Rotate if desired
            if rotation is not None:
                frame = cv2.rotate(frame, rotation)
            
            cv2.imwrite(img_path, frame)
        logger.debug(f"Saved image {img_path.name}")
    else:
        logger.warn(f"Unable to open video capture {camera_id}")
        

    try: 
        cap.release()
    except:
        pass

        return None

    return img_path

def selectCamera(name:str) -> int:
    """Run at the beginning of everytime the script is run to select the correct camera

    Args:
        name (str): Name of the printer to help with debugging and identifying which script is being run

    Returns:
        int: The camera number to use with cv2.VideoCapture
    """

     # Camera Selection
    camera_id = -1
    found = False
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.read()[0]:
            valid = False
            while valid is False:
                inp = input("Is the light on the desired camera on? y/n: ")
                if inp.strip().lower() == "y" or inp.strip().lower() == "yes":
                    camera_id = i
                    valid = True
                elif inp.strip().lower() == "n" or inp.strip().lower() == "no":
                    valid = True
                else:
                    print("Invalid input, please try again, yes or no.")
            
        cap.release()
        if camera_id != -1:
            break

    if camera_id == -1:
        print("No camera chosen, please check the connections")
    else:
        print(f"Camera {camera_id} chosen for printer {name}")

    return camera_id

def deleteImages(imgs_folder:pathlib.Path,fingerprint:str, max_images:int):
    """ Delete old images so as not to risk maxing out the storage

    Args:
        imgs_folder (pathlib.Path): Absolute path to the images folder where to save the images taken
        fingerprint (str): The fingerprint set for the camera token (set at the time of the first use of the Camera API Token)
        max_images (int): Max number of images allowed to be stored for this printer
    """
    imgs = list(imgs_folder.glob(f"{fingerprint}_*.jpg"))
    if len(imgs) > max_images:
        sorted_imgs = sorted(imgs, key = lambda x: datetime.datetime.strptime(x.stem[len(fingerprint)+1:], TIMESTAMP_FMT))
        for img in sorted_imgs[:-max_images]:
            img.unlink()
        logger.debug(f"Deleted {len(imgs)-max_images} image(s)")


def uncaughtExceptionsHandler(exc_type, exc_value, exc_traceback):
    """Make sure all exceptions get put in the log file for easy debugging
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    else:
        logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return


if __name__ == "__main__":
    sys.excepthook = uncaughtExceptionsHandler

    #Argparse
    args = parser.parse_args()

    ##Parse json file if its given
    if args.json is not None:
        with open(args.json) as f:
            config = json.load(f)

        printer_name = config["name"]
        fh = logging.FileHandler(f"{printer_name}.log")
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        token = config["token"]
        
        fingerprint = config["fingerprint"]
        if len(fingerprint) < 16:
            logging.exception("JSON Input: Fingerprint needs to be longer than 16 characters")
            raise ValueError("Fingerprint needs to be longer than 16 characters")
        ip = config["ip"]
        pl_api_key = config["apikey"]
        imgs_folder = pathlib.Path(config["directory"])

        try:
            possible_rot = [None, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE]
            if int(config["rotate"]/90) == config["rotate"]/90:
                rot_ind = int(config["rotate"]/90)
                image_rotation = possible_rot[rot_ind]
            else:
                logging.exception("JSON Input: User input with rotate needs to be a muliple of 90 degrees")
                raise TypeError(f"User input ({config['rotate']}) is not allowed, needs to be a multiple of 90")
        except KeyError:
            image_rotation = None

        #Max Images
        try:
            max_images = config["maximages"]
        except KeyError:
            max_images = DEFAULT_MAX_IMAGES

        #Image Folder
        if imgs_folder.exists():
            if imgs_folder.is_file():
                logging.exception("JSON Input: directory value already exists as a file, needs to be a folder")
                raise FileExistsError("Directory input already exists as a file, needs to be a folder")
        else:
            imgs_folder.mkdir(parents=True)

        #Select Camera
        try:
            camera_id = config["camera"]
            ret = CameraTester.verifyCamera(camera_id)
            if ret is False:
                logging.exception("JSON Input: Camera path provided could not be verified")
                raise ConnectionError("Argument supplied camera path is invalid, please select the camera manually by not passing in argument to -c or --camera or try a different absolute path. \n Sometimes cameras create multiple v4l devices so try other indicies (see readme)")
            else:
                camera_id = "/dev/v4l/by-id/" + camera_id
        except KeyError:
            camera_id = selectCamera(printer_name)


    ##JSON args is not passed
    else:
        printer_name = args.name
        fh = logging.FileHandler(f"{printer_name}.log")
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        token = args.token
        fingerprint = args.fingerprint
        possible_rot = [None, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE]

        if int(args.rotate) == float(args.rotate):
            if int(int(args.rotate)/90) == int(args.rotate)/90:
                rot_ind = int(int(args.rotate)/90)
                image_rotation = possible_rot[rot_ind]
            else:
                logging.exception("Argument Input: directory value already exists as a file, needs to be a folder")
                raise TypeError(f"User input ({args.rotate}) is not allowed, needs to be a multiple of 90")
            

        else:
            logging.exception("Argument Input: User input with rotate needs to be a muliple of 90 degrees")
            raise TypeError(f"User input ({args.rotate}) is not allowed, needs to be a multiple of 90")
        
        if len(fingerprint) < 16:
            logging.exception("Argument Input: Fingerprint needs to be longer than 16 characters")
            raise ValueError("Fingerprint needs to be longer than 16 characters")
        
        ip = args.ip
        pl_api_key = args.apikey
        imgs_folder = pathlib.Path(args.directory)
        max_images = int(args.maximages)
        if imgs_folder.exists():
            if imgs_folder.is_file():
                logging.exception("Argument Input: directory value already exists as a file, needs to be a folder")
                raise FileExistsError("Directory input already exists as a file, needs to be a folder")
        else:
            imgs_folder.mkdir(parents=True)

        #Select Camera
        if args.camera is None:
            camera_id = selectCamera(printer_name)
        else:
            camera_id = args.camera
            ret = CameraTester.verifyCamera(camera_id)
            if ret is False:
                logging.exception("JSON Input: Camera path provided could not be verified")
                raise ConnectionError("Argument supplied camera path is invalid, please select the camera manually by not passing in argument to -c or --camera or try a different absolute path. \n Sometimes cameras create multiple v4l devices so try other indicies (see readme)")
    

    #Infinite loop to get photos, and check printer status
    status = getPrinterStatus(ip, pl_api_key)
    if status is None: #Means the software couldn't connect to the printer
        printer_status = "IDLE"
    else:
        printer_status = status["printer"]["state"]
    

    while True:
        count = 0
        # Possible printer statuses can be found here: https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml#L1269
        #If the printer is printing
        while printer_status == "PRINTING":
            status = getPrinterStatus(ip, pl_api_key)
            if status is not None: #If the status check works properly change the state, otherwise do nothing
                printer_status = status["printer"]["state"]

            img_path = captureImage(camera_id, fingerprint, imgs_folder, image_rotation)
            if img_path is not None: #If the image was saved properly
                putImage(token, fingerprint, img_path)
            
            #Delete images every so often to reduce CPU load
            count += 1
            if count > 20:
                count = 0
                deleteImages(imgs_folder, fingerprint, max_images)

            time.sleep(60)


        #Printer is in any other state
        while printer_status != "PRINTING":
            status = getPrinterStatus(ip, pl_api_key)
            if status is not None: #If the status check works properly change the state, otherwise do nothing
                printer_status = status["printer"]["state"]

            img_path = captureImage(camera_id, fingerprint, imgs_folder, image_rotation)
            if img_path is not None:
                putImage(token, fingerprint, img_path)

            #Delete images every so often to reduce CPU load
            count += 1
            if count > 20:
                count = 0
                deleteImages(imgs_folder, fingerprint, max_images)

            time.sleep(120)

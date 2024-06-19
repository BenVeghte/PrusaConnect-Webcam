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

default_max_images = 500

#Can either supply configuration json file
parser = argparse.ArgumentParser(description="Use the arguments to pass the token and camera path to the script, can either use just json or the rest of them")
parser.add_argument("-t", "--token", help="Token created by Prusa Connect")
parser.add_argument("-n", "--name", help="Printer name to assist in debugging", default="printer")
parser.add_argument("-f", "--fingerprint", help="Unique fingerprint >16 characters long")
parser.add_argument("-i", "--ip", help="Local IP address of the printer to check print status")
parser.add_argument("-k", "--apikey", help="PrusaLink API key, found on printer settings page of prusa connect")
parser.add_argument("-d", "--directory", help="Absolute path to directory where to store images")
parser.add_argument("-m", "--maximages", help = "Maximum number of images for this camera to store in image folder", default = default_max_images)
parser.add_argument("-j", "--json", help="Absolute file path to configuration json file", default = None)



def putImage(token:str, fingerprint:str, img_path:pathlib.Path) -> requests.Response:
    snapshot_headers = {
        'Content-Type': 'image/jpg',
        'fingerprint': fingerprint,
        'token': token
    }

    URL = "https://connect.prusa3d.com/c/snapshot"

    with img_path.open(mode='rb') as f:
        image = f.read()
    
    resp = requests.put(url=URL, headers=snapshot_headers, data = image)

    return resp

def getPrinterStatus(ip:str, api_key:str) -> dict:
    resp = requests.get(url=f"http://{ip}/api/v1/status", headers = {"x-api-key":api_key})
    # print(resp.content.decode())
    return json.loads(resp.content)

def captureImage(camera_id:int, fingerprint:str, imgs_folder:pathlib.Path) -> pathlib.Path:
    #Capture image
    cap = cv2.VideoCapture(camera_id)
    ret, frame = cap.read()
    file_name = f"{fingerprint}_{datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S')}.jpg"
    img_path = imgs_folder/file_name
    cv2.imwrite(img_path, frame)
    cap.release()

    #Resize image
    width = 480
    img = Image.open(img_path)
    wpercent = (width / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((width, hsize), Image.Resampling.LANCZOS)
    img.save(str(file_name))

    print(f"Captured and saved image: {img_path.name}")

    return img_path

def selectCamera(name:str) -> int:
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
    os.chdir(str(imgs_folder))
    imgs = sorted(imgs_folder.iterdir(), key = os.path.getctime)
    filtered = []
    for img in imgs:
        if fingerprint in str(img) and ".jpg" in str(img):
            filtered.append(img)
    if len(filtered)>max_images: #If there are more images than the max allowed
        for img in filtered[0:-1*max_images]: #Deletes the oldest images until there are 500 remaining
            os.remove(str(img))


if __name__ == "__main__":
    #Argparse
    args = parser.parse_args()

    #JSON args is not passed
    if args.json is None:
        token = args.token
        printer_name = args.name
        fingerprint = args.fingerprint
        if len(fingerprint) < 16:
            raise ValueError("Fingerprint needs to be longer than 16 characters")
        ip = args.ip
        pl_api_key = args.apikey
        imgs_folder = pathlib.Path(args.directory)
        max_images = int(args.maximages)
        if imgs_folder.exists():
            if imgs_folder.is_file():
                raise FileExistsError("Images directory needs to be a folder, not a file")
        else:
            imgs_folder.mkdir(parents=True)
    else:
        with open(args.json) as f:
            config = json.load(f)
            
        token = config["token"]
        printer_name = config["name"]
        fingerprint = config["fingerprint"]
        if len(fingerprint) < 16:
            raise ValueError("Fingerprint needs to be longer than 16 characters")
        ip = config["ip"]
        pl_api_key = config["apikey"]
        imgs_folder = pathlib.Path(config["directory"])

        try:
            max_images = config["maximages"]
        except KeyError:
            max_images = default_max_images

        if imgs_folder.exists():
            if imgs_folder.is_file():
                raise FileExistsError("Images directory needs to be a folder, not a file")
        else:
            imgs_folder.mkdir(parents=True)

    
    #Select Camera
    camera_id = selectCamera(printer_name)

    #Infinite loop to get photos, and check printer status
    status = getPrinterStatus(ip, pl_api_key)
    # print(f"Prusa Link status response: {status}")
    printer_status = status["printer"]["state"]

    while True:
        #Send updated photo every minute and check for updated printer status
        while printer_status == "PRINTING":
            status = getPrinterStatus(ip, pl_api_key)
            # print(f"Prusa Link status response: {status}")
            printer_status = status["printer"]["state"]
            img_path = captureImage(camera_id, fingerprint, imgs_folder)
            putImage(token, fingerprint, img_path)
            time.sleep(60)

        
        #Check for updated printer status and upload images every 2 minutes while printer is idling or other state (possible states can be found here: https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml#L1269)
        while printer_status != "PRINTING":
            status = getPrinterStatus(ip, pl_api_key)
            # print(f"Prusa Link status response: {status}")
            printer_status = status["printer"]["state"] 
            img_path = captureImage(camera_id, fingerprint, imgs_folder)
            putImage(token, fingerprint, img_path)
            time.sleep(120)

# prusaconnect-webcam
Python script to use a usb connected webcam for prusa connect camera

## Usage
- Install required python packages with `pip install -r requirements.txt`

- Get configuration info for printers

    1. Camera Token can be found or created by clicking on your desired printer in PrusaLink, then the Camera tab, click add Camera (Other) and then copy the token.
        
        The fingerprint is linked with the token, if you are creating a new token, you can create a new fingerprint, if you are using an existing token that has already been used to send an image you must use that fingerprint, or delete the token and create a new one. 

    2. Get the API key for PrusaLink from the Settings page for your printer on PrusaConnect.
    3. Get the IP address for your printer: Can be found on the network settings page of your printer
- Create an images folder to store all the images and note the absolute path. 

    If you are running this script for multiple printers on the same computer, you can have one folder for each printer or one photo for all printers. The delete functionality only deletes photos associated with the printer the script is running for. 

- (Optional, but recommended, only works on linux) Identify which camera you want to use

    I have only tested this on Ubuntu 24 so no promises on any other OSs
    1. Run `python CameraTester.py`
        This will take a photo with all connected cameras and save it to the directory you ran the command from. Took at each image and see which one you want. The file name name will be what you pass into `prusacam.py` (minus the file extension)

- Option 1 (recommended): Create the JSON config file to run the script. 
    
    1. Use `example.json` as a template replacing the data with what you collected above
    2. Run the script with `python prusacam.py -j example.json`

- Option 2: Long command
    1. Run the script with the following command:
    
     ```
     python prusacam.py -t Your-Token -n Printer-Name -f Your-Fingerprint -i "192.168.XXX.XXX" -k PrusaLink-API-Key -d "absolute path to imgs folder" -m 1000 -c "usb-046d_C270_HD_WEBCAM_3B66D360-video-index0"
     ```

    This is not the recommended method because its just a long command and a slight pain to make sure everything is right

## Additional Notes
Passing the `-c` or `--camera` argument only works on linux

Regardless of whether you run the script with option 1 or 2, if you run the script in a linux environment I recommend you use screen so that the script remains running even when you exit the terminal window. 
    
There is a rotation feature incase you need or want to mount your camera upside down or rotated. Can only be done in increments of 90 degrees
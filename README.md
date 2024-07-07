# PrusaConnect USB Webcam
Program to use a USB connected webcam with PrusaConnect's camera feature. If you have multiple printers, you can run multiple instances of this script with different configuration files on the same computer.


## Usage

All commands are tested on a Raspberry Pi 4 (4GB RAM) with 64-bit Ubuntu 24.04 LTS (Noble Numbat) Server for an OS. 

Windows is also supported

- **Install required command line tools**

    *Linux Only*:
    `sudo apt-get install python3.12 python3.12-venv git ffmpeg libsm6 libxext6 -y`

- **Clone repository**

    *Both*:
    `git clone https://github.com/BenVeghte/PrusaConnect-Webcam.git`

- **Setup virtual environment**

    *Linux*:
    ```bash
    cd PrusaConnect-Webcam
    python3.12 -m venv venv
    source venv/bin/activate
    ```

    *Windows*:
    ```
    cd PrusaConnect-Webcam
    python3.12 -m venv venv
    venv/bin/activate
    ```
    Depending on how you installed Python on windows, the command might be just `python` as opposed to `python3.12`. Verify you are using the correct version with `python --version`


- **Install required python packages** 
 
    *Linux*:
    `pip install -r requirements.txt`

    *Windows*:
    `pip install -r requirements_windows.txt`


- **Get configuration info**

    1. Camera Token can be found or created by clicking on your desired printer in PrusaLink, then the Camera tab, click add Camera (Other) and then copy the token.
        
        The fingerprint is linked with the token, if you are creating a new token, you can create a new fingerprint, if you are using an existing token that has already been used to send an image you must use that fingerprint, or delete the token and create a new one. 

    2. Get the API key for PrusaLink from the Settings page for your printer on PrusaConnect.
    3. Get the IP address for your printer: Can be found on the network settings page of your printer

- **Create an images folder**

    If you are running this script for multiple printers on the same computer, you can have one folder for each printer or one photo for all printers. The delete functionality only deletes photos associated with the printer the script is running for. 

- **Camera Identification** (Optional, but recommended)

    I have only tested this on Ubuntu 24.04 LTS
    1. Run `python CameraTester.py`
        This will take a photo with all connected cameras and save it to the directory you ran the command from. Took at each image and see which one you want. The file name name will be what you pass into `prusacam.py` (minus the file extension)

    If you don't don't identify the camera like this, you can't automate the script like below in [Automation](#automation) as you need to use user input in the terminal to specify which camera to use each time on startup

- **JSON configuration file**
    
    1. Use `example.json` as a template replacing the data with what you collected above
    2. Run the script with `python prusacam.py -j example.json`

    This is not the recommended method because its just a long command and a slight pain to make sure everything is right. Also make sure that the `python` command points to the correct version of Python, this can be verified by running the command `python --version`. 

# Additional Notes

All output from the script gets saved to a file using the python `logging` library which sends it to a file `{printer name from configuration file or script arguments}.log`

Any commands I reference in this were tested on Ubuntu 24.04 LTS in bash. If you are doing this in another shell or OS, you might have to tweak the commands slightly, especially the ones where the proper libraries are installed

The `-c` or `--camera` argument is quite OS specific, I suspect that its one of the parts of the script most likely to break on other OSs as it uses the /dev/v4l/by-id/ path to connect to the camera

Regardless of whether you run the script with option 1 or 2, if you run the script in a linux environment I recommend you use screen so that the script remains running even when you exit the terminal window. 
    
There is a rotation feature incase you need or want to mount your camera upside down or rotated. Can only be done in increments of 90 degrees

I recommend running the script manual from the console the first time to make sure all libraries are properly installed.



# Common Issues
**ImportError**

Shows up in the form of `ImportError: libGL.so.1` or similar. This is because opencv2 relies on a couple extra tools that aren't always installed in an OS.

Run `sudo apt-get install ffmpeg libsm6 libxext6` in your terminal to install the required libraries (taken from [this StackOverflow thread](https://stackoverflow.com/questions/55313610/importerror-libgl-so-1-cannot-open-shared-object-file-no-such-file-or-directo]))

**Images not appearing in PrusaConnect**

The most likely cause is that the computer you are running this on can't connect to your network. Check the log file, which can be found with the name `{printer name from configuration file or script arguments}.log` for example `Printer1.log`.

`prusacam.py` will not exit out with an error if prusalink or prusaconnect requests get timed out as my Raspberry Pi occasionally randomly disconnects from the network and I didn't want to have to worry about restarting it every time there was a `requests.exceptions.ConnectTimeout` error. 

Most other causes for this happening (i.e. an incorrect token or fingerprint) will throw an error which can also be seen in the log file. 

# Automation

To automate running of the script, I created a shell script that I made a cronjob to run at reboot to startup an instance of the script for all 3 of my printers.

```bash
#!/bin/bash
cd /home/ubuntu/PrusaConnect-Webcam
git pull

venv/bin/pip install -r requirements.txt

venv/bin/python prusacam.py -j Printer1.json &
venv/bin/python prusacam.py -j Printer2.json &
venv/bin/python prusacam.py -j Printer3.json &

```
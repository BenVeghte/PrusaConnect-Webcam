import os
import subprocess
import cv2

def verifyCamera(identifier: str | int) -> bool:
    if os.name == "nt":  # Windows
        camera_path = int(identifier)
    else:  # Linux
        camera_path = "/dev/v4l/by-id/" + str(identifier)

    cap = cv2.VideoCapture(camera_path)
    if cap.isOpened():
        cap.release()
        return True
    else:
        return False

def allCameraSnapshot():
    if os.name == "posix":  # Linux
        result = subprocess.run(["ls", "/dev/v4l/by-id/"], stdout=subprocess.PIPE).stdout.decode("utf-8").replace("\n", " ")
        v4l_devices = result.strip().split(" ")
        for camera_id in v4l_devices:
            camera_path = "/dev/v4l/by-id/" + camera_id
            cap = cv2.VideoCapture(camera_path)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    cv2.imwrite(f"{camera_id}.jpg", frame)
                    print(camera_id)
            cap.release()
    elif os.name == "nt":  # Windows
        for index in range(10):  # Try the first 10 indices.
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    filename = f"camera_{index}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"Captured {filename}")
                cap.release()

    print(f"All photos captured to {os.getcwd()}")

if __name__ == "__main__":
    print("Taking a photo from all connected cameras")
    allCameraSnapshot()
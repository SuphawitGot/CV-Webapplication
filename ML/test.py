from ultralytics import YOLO # type: ignore
import cv2
import math 

cap = cv2.VideoCapture("D:\\Github repo\\PROJECT\\CV-Webapplication\\ML\\test-sample1.mp4")
model = YOLO("yolo26n.pt")

while True:
    success, frame = cap.read()
    # print("Frame read success:", success, "| Frame is None:", frame is None)  
    result = model.track(frame, stream=True,classes=[2],verbose=False, tracker="bytetrack.yaml")    
    for r in result:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2) #tranfrom into integer 
            conf = math.ceil((box.conf[0]*100))/100
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    if not success or frame is None:
        print("ERROR: Failed to read frame")
        break
        # 4. Display the resulting frame
    cv2.imshow('Webcam Feed', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()  # ← always release the capture
cv2.destroyAllWindows()
from ultralytics import YOLO # type: ignore
import cv2
import supervision as sv # type: ignore
from ultralytics import solutions # type: ignore
import math 
import numpy as np

cap = cv2.VideoCapture(0)
model = YOLO("yolo26n.pt")
print(model.names)
while True:
    success, frame = cap.read()
    # print("Frame read success:", success, "| Frame is None:", frame is None)  
    
    if not success or frame is None:
        print("ERROR: Failed to read frame")
        break
    car = model.track(frame,classes=[2],verbose=False, tracker="bytetrack.yaml")
    MotorCycle = model.track(frame,classes=[3],verbose=False, tracker="bytetrack.yaml") 
    crosswalk = model.train(data="coco8.yaml", epochs=100, imgsz=640)
    for c in car:
        boxes = c.boxes
        if boxes is not None:
            continue
        for box in boxes:
            x1, y1, x2, y2 = boxes.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            conf = math.ceil(boxes.conf[0] * 100) / 100
            id = int(boxes.id[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
    for m in MotorCycle:
        boxes = m.boxes
        if boxes is not None:
            continue
        for box in boxes:
            x1, y1, x2, y2 = boxes.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            conf = math.ceil(boxes.conf[0] * 100) / 100
            id = int(boxes.id[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # 4. Display the resulting frame
    cv2.imshow('Webcam Feed', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()  # ← always release the capture
cv2.destroyAllWindows()


from ultralytics import YOLO # type: ignore
import cv2
import supervision as sv # type: ignore
from ultralytics import solutions # type: ignore
import math 
import numpy as np

cap = cv2.VideoCapture(r"D:\\Github repo\\PROJECT\\CV-Webapplication\\ML\\test-sample1.mp4")
car_model = YOLO("yolo26n.pt")
crosswalk_model = YOLO(r"D:\\Github repo\\PROJECT\\CV-Webapplication\\runs\detect\\crosswalk_model\\weights\\best.pt")

while True:
    success, frame = cap.read()
    car = car_model.track(frame,classes=[2],verbose=False, tracker="bytetrack.yaml")
    MotorCycle = car_model.track(frame,classes=[3],verbose=False, tracker="bytetrack.yaml") 
    crosswalk = crosswalk_model(frame,verbose=False,tracker="bytetrack.yaml")
    for c in car:
        boxes = c.boxes
        for box in  boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            conf = math.ceil(box.conf[0] * 100) / 100
            id = int(box.id[0]) if box.id is not None else -1
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    for m in MotorCycle:
        box = m.boxes
        for box in m.boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            conf = math.ceil(box.conf[0] * 100) / 100
            id = int(box.id[0]) if box.id is not None else -1
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    for cw in crosswalk:
        box = cw.boxes
        for box in cw.boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            conf = math.ceil(box.conf[0] * 100) / 100
            if conf > 0.5:  # ← only draw if confidence is above 0.5
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, f"Crosswalk {conf:.2f}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # 4. Display the resulting frame
    cv2.imshow('Webcam Feed', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()  # ← always release the capture
cv2.destroyAllWindows()

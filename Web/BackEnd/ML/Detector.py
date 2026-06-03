from ultralytics import YOLO # type: ignore
import os
import cv2
import math 
import numpy as np
import easyocr
import os
#rom main import is_running, is_paused 


reader = easyocr.Reader(['en'])
cap = cv2.VideoCapture(r"ML\\test-sample1.mp4")
model = YOLO("yolo26n.pt")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
crosswalk_model = YOLO(os.path.join(BASE_DIR, "best.pt"))

car_in_crosswalk = 0 
midpoint_x = 0
midpoint_y = 0
car_box    = None  # ← store last car box for cropping


def process_frame(frame, is_running, is_paused):
    global car_in_crosswalk, midpoint_x, midpoint_y, car_box

    success, frame = cap.read()

    if not success or frame is None:
        return None
    
    car       = model.track(frame, classes=[2], verbose=False, tracker="bytetrack.yaml")
    MotorCycle= model.track(frame, classes=[3], verbose=False, tracker="bytetrack.yaml")
    crosswalk = crosswalk_model(frame, verbose=False)

    for c in car:
        for box in c.boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            conf = math.ceil(box.conf[0] * 100) / 100
            if conf > 0.5: # --> check accuracy
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"Car {conf}", (x1, y1 - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (99, 49, 222), 2)
                midpoint_x = (x1 + x2) // 2
                midpoint_y = y2 
                car_box = (x1, y1, x2, y2)  # ← save box
                cv2.circle(frame, (midpoint_x, midpoint_y), 6, (0, 0, 255), cv2.FILLED)  # ← dot

    for m in MotorCycle:
        for box in m.boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            conf = math.ceil(box.conf[0] * 100) / 100
            if conf > 0.5:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"Motorcycle {conf}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (99, 49, 222), 2)
                midpoint_x = (x1 + x2) // 2
                midpoint_y = y2
                car_box = (x1, y1, x2, y2)
                cv2.circle(frame, (midpoint_x, midpoint_y), 6, (0, 0, 255), cv2.FILLED)  # ← dot

    for cw in crosswalk:
        for box in cw.boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            conf = math.ceil(box.conf[0] * 100) / 100
            if conf > 0.5:
                crosswalk_zone = np.array([[x1,y1],[x2,y1],[x2,y2],[x1,y2]], dtype=np.int32)
                is_inside = cv2.pointPolygonTest(crosswalk_zone, (float(midpoint_x), float(midpoint_y)), False)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, f"Crosswalk {conf}", (x1, y1 - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                # if is_inside >= 0 and is_running and car_box:
                car_in_crosswalk += 1
                cv2.imwrite(f"captures/car_{car_in_crosswalk}.jpg", frame)

                    # ← crop and read plate
                bx1, by1, bx2, by2 = car_box
                cropped = frame[by1:by2, bx1:bx2]
                result = reader.readtext(cropped)
                for (_, text, prob) in result:
                    if prob > 0.5:
                        print(f"Plate: {text} ({prob:.2f})")
                        cv2.putText(frame, text, (bx1, by1 - 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)


    cv2.imshow('Webcam Feed', frame)
    return frame
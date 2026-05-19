
from ultralytics import YOLO # type: ignore
# C:\Users\Suphawit\AppData\Roaming\Ultralytics\
def train_model():
    model = YOLO("yolo26n.pt")
    results = model.train(
        data=r"ML\\datasetcrosswalk\\data.yaml",
        epochs=100,
        imgsz=640,
        batch=16,
        name="crosswalk_model"
    )


if __name__ == '__main__':
    train_model()
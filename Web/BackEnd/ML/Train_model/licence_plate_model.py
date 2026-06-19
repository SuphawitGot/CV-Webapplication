from ultralytics import YOLO # type: ignore
def train_model():
    model = YOLO("yolo26n.pt")
    results = model.train(
        data=r"D:\\Dataset\\Licence_Plate\\data.yaml",
        epochs=60,
        imgsz=640,
        batch=16,
        name="LC.pt"
    )

if __name__ == '__main__':
    train_model()
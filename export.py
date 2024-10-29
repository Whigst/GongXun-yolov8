from ultralytics import YOLO

# Load a model
model = YOLO("models/cirAndMat.pt")  # load an official model

# Export the model
model.export(format="engine", half=True, imgsz=320, workspace=1)

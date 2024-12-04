from ultralytics import YOLO

# Load a model
model = YOLO("models/cirAndMat_2.pt")  # load an official model

# Export the model
model.export(format="engine", half=True, imgsz=640, workspace=1)

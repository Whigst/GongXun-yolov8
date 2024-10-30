from ultralytics import YOLO

# Load a pretrained YOLO11n model
model = YOLO("models/cirAndMat.pt")

# Run inference on an image
results = model("ultralytics/assets/50.jpg")  # results list

# View results
i = 0 
for r in results:
    print(f"frame {i}: {r.boxes}")  # print the Boxes object containing the detection bounding boxes
    i += 1
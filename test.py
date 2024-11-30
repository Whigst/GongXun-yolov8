from ultralytics import YOLO

# Load a pretrained YOLO11n model
model = YOLO("models/cirAndMat.pt")

# Run inference on an image
results = model("ultralytics/assets/50.jpg")  # results list

# View results
p = (0, 1)
l = p
for i in l:
    print(i)
i = 0 
for r in results:
    #print(f"frame {i}: {r.boxes}")  # print the Boxes object containing the detection bounding boxes
    for box in r.boxes:
        # print(f"{r.names[0]}")
        print(r.names[box.cls.item()])
        x1, y1, x2, y2 = box.xyxy.tolist()[0]
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        print(f"Center coordinates: ({center_x}, {center_y})")# 判断检测结果是reditem, greenitem, blueitem
        itemColorFlag = 0
        if r.names[0] == 'redItem':
            itemColorFlag = 1
        elif r.names[0] == 'greenItem':
            itemColorFlag = 2
        elif r.names[0] == 'blueItem':
            itemColorFlag = 3
        print(f"Item color flag: {itemColorFlag}")
    i += 1
import cv2

image_path = r"C:\Users\wargriff\Pycharm_Project_v 3.12\Pac-Man\assets\fruits\cerise.png"

image = cv2.imread(image_path)
if image is None:
    print("❌ Image introuvable")
    exit()

scale = 5
img = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
clone = img.copy()

points = []

def click(event, x, y):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"Point {len(points)} :", x, y)

cv2.namedWindow("image")
cv2.setMouseCallback("image", click)

print("🖱️ Clique 2 points : source puis destination | S = appliquer")

while True:
    cv2.imshow("image", img)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("s") and len(points) >= 2:
        break

cv2.destroyAllWindows()

(src_x, src_y) = points[0]
(dst_x, dst_y) = points[1]

size = 40

h, w = img.shape[:2]

# 🔥 CLAMP (empêche de sortir de l'image)
def clamp(val, minv, maxv):
    return max(minv, min(val, maxv))

# Source
x1s = clamp(src_x - size, 0, w)
x2s = clamp(src_x + size, 0, w)
y1s = clamp(src_y - size, 0, h)
y2s = clamp(src_y + size, 0, h)

# Destination
x1d = clamp(dst_x - size, 0, w)
x2d = clamp(dst_x + size, 0, w)
y1d = clamp(dst_y - size, 0, h)
y2d = clamp(dst_y + size, 0, h)

# 🔥 Ajuster tailles pour correspondre
patch = clone[y1s:y2s, x1s:x2s]

h_patch, w_patch = patch.shape[:2]

img[y1d:y1d+h_patch, x1d:x1d+w_patch] = patch

# 🔽 retour taille normale
result = cv2.resize(img, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_AREA)

cv2.imwrite("result.png", result)

print("🔥 Copier-coller réussi → result.png")
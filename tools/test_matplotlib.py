import matplotlib.pyplot as plt
from PIL import Image
img = Image.open('stinkbug.png')  # opens the file using Pillow - it's not an array yet
img.thumbnail((64, 64), Image.ANTIALIAS)  # resizes image in-place

fig = plt.figure()

imgplot = plt.imshow(img, interpolation="bicubic")

rectangle = plt.Rectangle((10, 10), 100, 100, fc='r')

plt.gca().add_path(rectangle)


fig.savefig('stinktriangle.png', orientation='landscape',
                    bbox_inches='tight')
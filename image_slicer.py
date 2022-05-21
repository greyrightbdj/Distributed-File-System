
from math import ceil
from PIL import Image
import numpy

def chunk_image(img_name,num_chunks):  
    chunks = []
    img= Image.open(img_name)
    np_img = numpy.array(img)

    windowsize_r = int(ceil(np_img.shape[0]/num_chunks))
    for r in range(0,np_img.shape[0], windowsize_r):
        window = np_img[r:r+windowsize_r,:]
        chunks.append(window)
    return chunks
        

def combine_image(chunks):  
    return numpy.concatenate(chunks)

chunks = chunk_image('Food2.jpg',10)
window = combine_image(chunks)
data = Image.fromarray(window)
data.save('combined.jpg')

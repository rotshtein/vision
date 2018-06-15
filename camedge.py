import cv2
import numpy as np
from matplotlib import pyplot as plt

def PrintHelp():
    print '  Use w,x to change  the Canny max thresholds'
    print '  Use a,d to change  the Canny min thresholds'

    print '  Use j,l to change the GaussianBlur kernel size'
    print '  Use m,i to change the GaussianBlur standard deviation'

    print '  Esc (when one of the windows are in focus) to exit'
#img = cv2.imread('messi5.jpg',0)

def FindEdge():
    cv2.namedWindow("Captured Image")
    cv2.namedWindow("Edge Image")
    cam = cv2.VideoCapture(0)
    min = 27
    max = 30
    kernel_size = 5
    deviation = 3

    while(True):
        ret, img = cam.read()
        img = cv2.GaussianBlur(img, (kernel_size,kernel_size), deviation)
        edges = cv2.Canny(img,float(min),float(max))

        '''
        plt.subplot(121),plt.imshow(img,cmap = 'gray')
        plt.title('Original Image'), plt.xticks([]), plt.yticks([])
        plt.subplot(122),plt.imshow(edges,cmap = 'gray')
        plt.title('Edge Image'), plt.xticks([]), plt.yticks([])
        
        plt.show()
        '''
        cv2.putText(edges, "min=%d, max=%d" %(min,max), (30,50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (255,255,0), 1);
        cv2.putText(edges, "Kernel size=%d, deviation=%d" %(kernel_size,deviation), (30,70), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (255,255,0), 1);
        cv2.imshow("Captured Image",img)
        cv2.imshow('Edge Image',edges)
        
        k = cv2.waitKey(1)
        if k%256 == 27:
            # ESC pressed
            print("Escape hit, closing...")
            break
        if k %256 == 119:
            max = max + 1
           
        if k %256 == 120:
            max = max - 1
                
        if k %256 == 97:
            min = min - 1

        if k %256 == 100:
            min = min + 1
            
        if k %256 == 106:
            kernel_size = kernel_size - 2
            if (kernel_size < 1):
                kernel_size = 1

        if k %256 == 108:
            kernel_size = kernel_size + 2
            
        if k %256 == 109:
            deviation = deviation - 1
            if (deviation < 1):
                deviation = 1

        if k %256 == 105:
            deviation = deviation + 1
        
            
    cam.release()
    cv2.destroyAllWindows()
    
def main():
    PrintHelp()
    FindEdge()

if __name__ == "__main__":
    main()


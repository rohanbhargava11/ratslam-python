from pylab import *
import time
from PIL.Image import Image
from scipy.spatial.distance import cityblock
def get_im_xSums(im, y_range_type, x_range):

    #gets the scanline intensity which is returned as im_xsums of the sub_image specified by the parameters initialized in the constructor
    
    sub_im = im[y_range_type, x_range] 
    im_xsums = asarray(sum(sub_im, 0), dtype = 'float64')
    im_xsums = im_xsums/(sum(im_xsums)/ len(im_xsums)) 
    return im_xsums

def compare_segments_image(seg1, seg2, slen, cwl):
	#return 2
	#for i in range(slen):
	#	seg1[:,i:60+i]
	#tmp=seg1[:,5:55] # seg is 50 by 10
	#for i in range(slen):
	#print 'template size',seg2.shape
	#print 'template',seg2[:,5:55]
	#print citblock(seg1[:,0:50],seg2[:,5:55])
	dist=[]
	#print seg2.shape
	#print seg1.shape
	for i in range(10):
		
		
		#print 'seg 1 shape',a.shape
		dist.append(cityblock(seg1[:,i:50+i].flatten(),seg2.flatten()))
		
	return min(dist)		
def compare_segments(seg1,seg2,slen,cwl):
	
	
    # assume a large difference
    mindiff = inf
        
    # for each offset, sum the abs difference between the two segments
    for offset in xrange(slen+1):
        cdiff = abs(seg1[offset:cwl] - seg2[:cwl - offset])
        cdiff = float(sum(cdiff, 0)) / float(cwl - offset)
        if (cdiff < mindiff):
            mindiff = cdiff
            minoffset = offset
            
    for offset in xrange(1, slen+1):
        cdiff = abs(seg1[:cwl - offset] - seg2[offset:cwl])
        cdiff = sum(cdiff, 0) / float64(cwl - offset)
        if (cdiff < mindiff):
            mindiff = cdiff
            minoffset = -(offset)
    offset = minoffset
    sdif = mindiff
    
    return (offset, sdif)
    
class SimpleVisualOdometer:
    "Very simple visual odometry machinery"

    def __init__(self, **kwargs):
        
        self.prev_vrot_image_x_sums = kwargs.pop('prev_vrot_image_x_sums', zeros(281))
        self.prev_vtrans_image_x_sums = kwargs.pop('prev_vtrans_image_x_sums', zeros(281))
        self.IMAGE_ODO_X_RANGE = kwargs.pop('IMAGE_ODO_X_RANGE', slice(194, 475))
        self.IMAGE_VTRANS_Y_RANGE = kwargs.pop('IMAGE_VTRANS_RANGE', slice(269, 430))
        self.IMAGE_VROT_Y_RANGE = kwargs.pop('IMAGE_VROT_Y_RANGE', slice(74, 240) )
        self.VTRANS_SCALE = 100
        self.VISUAL_ODO_SHIFT_MATCH = 140 
        
        self.odo = [0.0,0.0, pi/2]
        self.delta = [0,0] #[vtrans, vrot]
        
    def update(self, im):
        """ Estimate the translation and rotation of the viewer, given a new 
            image sample of the environment
            
            (Matlab version: equivalent to rs_visual_odometry)
        """
        
        FOV_DEG = 50.0
        dpp = float64(FOV_DEG) / im.shape[0]

        # vtrans 
        sub_image = im[self.IMAGE_VTRANS_Y_RANGE, self.IMAGE_ODO_X_RANGE]

        image_x_sums = sum(sub_image, 0)
        avint = float64(sum(image_x_sums)) / len(image_x_sums)
        image_x_sums = image_x_sums/avint
        
        [minoffset, mindiff] = compare_segments(image_x_sums, 
                                                self.prev_vtrans_image_x_sums, 
                                                self.VISUAL_ODO_SHIFT_MATCH, 
                                                len(image_x_sums))
        vtrans = mindiff * self.VTRANS_SCALE
        
        # a hack to detect excessively large vtrans
        if vtrans > 5:
            vtrans = 0

        self.prev_vtrans_image_x_sums = image_x_sums
        
        # vrot
        sub_image = im[self.IMAGE_VROT_Y_RANGE, self.IMAGE_ODO_X_RANGE]
        image_x_sums = sum(sub_image, 0)
        avint = float64(sum(image_x_sums)) / len(image_x_sums)
        image_x_sums = image_x_sums/avint
        
        [minoffset, mindiff] = compare_segments(image_x_sums, 
                                                self.prev_vrot_image_x_sums, 
                                                self.VISUAL_ODO_SHIFT_MATCH, 
                                                len(image_x_sums))
        vrot = minoffset * dpp * pi / 180.0
                
        self.prev_vrot_image_x_sums = image_x_sums
        
        self.odo[2] += vrot 
        self.odo[0] += vtrans* cos(self.odo[2]) #xcoord 
        self.odo[1] += vtrans* sin(self.odo[2]) #ycoord    
        
        self.delta = [vtrans, vrot]
        
        return self.odo


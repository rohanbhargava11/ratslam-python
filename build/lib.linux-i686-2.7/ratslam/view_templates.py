from numpy import *
from visual_odometer import compare_segments_image

import numpy as np
#import simple_vision

from visual_odometer import compare_segments
import cv2


class ViewTemplate (object):
       
    def __init__(self, x_pc, y_pc, z_pc):
        self.x_pc = x_pc
        self.y_pc = y_pc
        self.z_pc = z_pc
        self.exps = []
         
    def match(self, input_frame):
        raise NotImplemented


class IntensityProfileTemplate(ViewTemplate):
    """A very simple view template as described in Milford and Wyeth's 
       original algorithm.  Basically, just compute an intensity profile 
       over some region of the image. Simple, but suprisingly effective
       under certain conditions
       
    """
    
    def __init__(self, input_frame, x_pc, y_pc, z_pc,
                       y_range, x_range, shift_match):
        
        ViewTemplate.__init__(self, x_pc, y_pc, z_pc)
        
        self.x_range = x_range
        self.y_range = y_range
        self.shift_match = shift_match
        
        self.first = True
        self.activity=1.0
        # compute template from input_frame
        #print 'here'
        self.template = self.convert_frame(input_frame)
        

    def convert_frame(self, input_frame):
        "Convert an input frame into an intensity line-profile"
        '''
        sub_im = (input_frame[self.y_range, self.x_range]).astype('float')
        cv2.resize(sub_im,sub_im.shape,
        #cv2.imshow('hello',sub_im)
        #cv2.waitKey(1)
        # normalised intensity sums 
        image_x_sums = sum(sub_im, 0)
        #print 'sum is', image_x_sums
        image_x_sums = image_x_sums / sum(image_x_sums)
        #print 'final sum is',image_x_sums
        '''
        image_x_sums=cv2.resize(input_frame,(60,10),interpolation=cv2.INTER_AREA).astype('float')
        #print image_x_sums.shape
        #image_x_sums=image_x_sums[:,5:55]
        image_x_sums=image_x_sums/sum(image_x_sums)
        #print 'internsity',image_x_sums
        return image_x_sums
    
    def match(self, input_frame):
	#cv2.imshow('hello',input_frame)
     #   cv2.waitKey(1)
        #print'Return a score for how well the template matches an input frame'
        #print 'I am in match called by match in view_temaplates'
        image_x_sums = self.convert_frame(input_frame)
        #print 'the intensity',image_x_sums
        #print 'the template',self.template
        #print 'size is of seg 2',self.template.shape
        #toffset, 
        
        tdiff = compare_segments_image(image_x_sums, 
                                        self.template, 
                                        self.shift_match,
                                        image_x_sums.shape[0])
        #print 'difference',tdiff                               
        return tdiff #* len(image_x_sums)

    
class ViewTemplateCollection (object):
    """ A collection of simple visual templates against which an incoming
        frame can be compared.  The entire collection of templates is matched
        against an incoming frame, and either the best match is returned, or
        a new template is created from the input image in the event that none
        of the templates match well enough
        
        (Matlab equivalent: rs_visual_template)
    
    """
        
        
    def __init__(self, template_generator, match_threshold, global_decay):
        """
        Arguments:
        template_generator -- a callable object that generates a ViewTemplate
                              subclass
        match_threshold -- the threshold below which a subtemplate's match
                           is considered "good enough".  Failure to match at
                           this threshold will result in the generation of a 
                           new template object
        global_decay -- not currently used
        
        """
        self.template_generator = template_generator
        self.global_decay = 0.1#global_decay # need to set this
        self.match_threshold = match_threshold
	self.active_decay=1.0 # need to set this
        self.templates = []
        self.current_template = None
	self.match_scores=[]
    
    def __getitem__(self, index):
        return self.templates[index]
    
    def match(self, input_frame, x, y, th):
        #cv2.imshow('hello',input_frame)
        #cv2.waitKey(1)
        #print 'I am in match called by simulation'
        for i in self.templates:
			i.activity=i.activity-self.global_decay
			if i.activity<0:
				i.activity=0
        self.match_scores = [ t.match(input_frame) for t in self.templates]
        print 'the score is',self.match_scores#,match_scores[0]
        if len(self.match_scores) == 0 or min(self.match_scores) > self.match_threshold:
            print 'no matches, so build a new one'
            new_template = self.template_generator(input_frame, x, y, th)# you might want to resize here
            new_template.first=True
            new_template.activity=self.active_decay
            #print 'new templae',new_template.template
            new_template.template=new_template.template[:,5:55]
            #print 'new template size',new_template.template.shape
            self.templates.append(new_template)
            #print 'I am out of here'
            
            return new_template#,match_scores
	    
        else:
			print 'we have a match'
			      
			best_template = self.templates[argmin(self.match_scores)]
			best_template.first=False
			best_template.activity=best_template.activity+self.active_decay
			#print match_scores[0]
			return best_template#,match_scores
       
       
       
    def return_match_scores(self):
       return self.match_scores
	#return min(match_scores)		
        

                

from ratslam import (ViewTemplateCollection,
                     IntensityProfileTemplate,
                     PoseCellNetwork,
                     ExperienceMap,
                     SimpleVisualOdometer)

import os, os.path
import csv
import time
from functools import partial

from itertools import imap
from pylab import  *
import numpy
import cv2

#import line_profiler

class RatSLAM (object):
    
    def __init__(self, image_source):
        self.image_source = image_source
            
        pc_shape = [30,30,36]
        
        self.view_templates = self.initialize_view_templates(pc_shape)
        self.visual_odometer = self.initialize_odo()
        self.pose_cell_network = self.initialize_pose_cell_network(pc_shape)
        self.experience_map = self.initialize_experience_map()
        
        self.time_step = 0
        
    #creating visual templatecollection and initializing it with the first image.
    def initialize_view_templates(self, pc_shape):
    
        simple_template = partial(IntensityProfileTemplate,
                                  x_range = slice(54,615),
                                  y_range = slice(119,280),
                                  shift_match=20)
        print 'Simple template is',simple_template                         
        templates = ViewTemplateCollection(simple_template,
                                           global_decay=0.1,
                                           match_threshold=0.2)
        im = self.image_source
        #templates.update(zeros(561))
        
        templates.curr_vc = templates.match(im, pc_shape[0]/2.0,
                                                pc_shape[1]/2.0,
                                                pc_shape[2]/2.0 )
        
        return templates

    #initializing Visual Odometer
    def initialize_odo(self):
        im0 = self.image_source
        vod = SimpleVisualOdometer()
        vod.update(im0)
        return vod
        
    #initializing position of the pose cell network activity bubble at center
    def initialize_pose_cell_network(self, pc_shape):

        pcnet = PoseCellNetwork(pc_shape)
        xy_pc = pc_shape[0]/2+1 
        th_pc = pc_shape[2]/2+1 
        
        pcnet.posecells[xy_pc, xy_pc, th_pc] = 1 # initalize the matrix with shape

        v_temp = self.view_templates[0]
        pcnet.update(self.visual_odometer.delta, v_temp) #determines the effect of visual template on poe cell network
        #pcmax = pcnet.get_pc_max(pcnet.avg_xywrap, pcnet.avg_thwrap)
		# I think so it doesn't plot all the activites because it only reutrns the mzximum value of pose cell index 
		# and we need to get it return all the pose cell activity so that I can understand the pattern.
        return pcnet

    def initialize_experience_map(self):

        emap = ExperienceMap(exp_loop_iter=100)
        
        current_vt = self.view_templates.curr_vc
        
        emap.update(self.visual_odometer.delta[0], 
                    self.visual_odometer.delta[1], 
                    self.pose_cell_network.max_pc[0], 
                    self.pose_cell_network.max_pc[1], 
                    self.pose_cell_network.max_pc[2], 
                    current_vt)
        
        return emap

    #@property
    def current_exp(self):
        return self.experience_map.current_exp

    #@profile
    def evolve(self,image):
        c = self.time_step
        self.time_step += 1
        
        self.current_image = image#self.image_source[c]
        
        avg_xywrap = self.pose_cell_network.avg_xywrap
        avg_thwrap = self.pose_cell_network.avg_thwrap
        pcmax = self.pose_cell_network.get_pc_max(avg_xywrap, avg_thwrap)
        #print 'entering visual template'
        
        # get visual template
        v_temp= self.view_templates.match(self.current_image, pcmax[0],
                                                           pcmax[1],
                                                           pcmax[2])
        
	match_scores=self.view_templates.return_match_scores()
	print min(match_scores)
	#print v_temp,v_temp.first,rohan
        # get odometry
        self.current_odo = self.visual_odometer.update(self.current_image)
        print self.current_odo

        #get pcmax
        pcmax,b,arg_visual_cell,posecells_1=self.pose_cell_network.update(self.visual_odometer.delta, v_temp) 
        #pcmax = self.pose_cell_network.get_pc_max(self.pose_cell_network.avg_xywrap, 
#                                                  self.pose_cell_network.avg_thwrap)
        #if a==pcmax:
		#	print 'it is equal'
		
        self.current_pose_cell = pcmax
        self.all_pose_cell=b
        self.args_visual_posecells=arg_visual_cell
        self.posecells_1=posecells_1
        self.match_scores=match_scores
        
        self.experience_map.update(self.visual_odometer.delta[0], 
                                   self.visual_odometer.delta[1], 
                                   pcmax[0], pcmax[1], pcmax[2],
                                   v_temp)
	#print b

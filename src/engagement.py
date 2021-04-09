#!/usr/bin/env python
# -*- encoding: UTF-8 -*-

import os
import sys

sys.path.append(os.path.dirname(__file__) + "/../pyLib/")
from tablet import tabletShowText
from collections import deque
from collections import Counter

import qi
import rospy
from rospy.timer import sleep
from std_msgs.msg import Int8, String
from naoqi import ALProxy

logger = qi.Logger("face-tracking-node")

TIMEOUT=10 #s

faceS = [0,0,0,0,0,0,0,0]
gazeS = [0,0,0,0,0,0,0,0]
facenameS=['...','...','...','...','...','...','...','...','...','...',]

class FaceTracking():
    def __init__(self):
        self.faces = 0
        self.gaze = 0
        self.gaze_tolerance = 0.5
        self.near = 0
        self.name = '...'
        self.currentState = 'unknowState'
        self.bIsRunning = False
        self.delayed = []
        self.session = qi.Session()

        try:
            self.session.connect("tcp://" + Robot_IP + ":" + Robot_Port)
        except RuntimeError:
            print ("Can't connect to Naoqi at ip " + Robot_IP + " on port " + Robot_Port + "\n Please check your script arguments. Run with -h option for help.")
            sys.exit(1)

        self.awareness = self.session.service('ALBasicAwareness')
        self.memory = self.session.service("ALMemory")
        self.gaze_analysis = self.session.service("ALGazeAnalysis")
        self.behavior = self.session.service("ALBehaviorManager")
        self.face_detection = self.session.service("ALFaceDetection")
        self.engagement_zones = self.session.service("ALEngagementZones")
        
        self.awareness.setEngagementMode(rospy.get_param('engMode')) # cf http://doc.aldebaran.com/2-5/naoqi/peopleperception/albasicawareness.html
        self.awareness.setTrackingMode(rospy.get_param('trackMode')) # only use head to track
        self.awareness.setStimulusDetectionEnabled('People', True)
        self.tabShow = rospy.get_param('tabShow')

        self.awareness.setEnabled(True)
        
        try:
            self.behavior.runBehavior("lookingup/behavior_1", _async=True)
            self.face_detection.setRecognitionEnabled(True)
        except:
            logger.warning("LookingUp error.")
        
        logger.info("ROS Node started")


    def close(self):
        self.faces = 0
        self.gaze = 0
        self.name = '...'        
        self.bIsRunning = False
        self.awareness.setEnabled(False)
        self.behavior.stopBehavior("lookingup/behavior_1")


    def detect(self):
        self.bIsRunning = True
        self.name = '...'
        self.gaze = 0
        self.gaze_analysis.setTolerance(self.gaze_tolerance)
        while self.bIsRunning:
            ids = self.memory.getData("PeoplePerception/PeopleList")
            self.faces = len(ids)
            if self.faces < 4:
                #identify user
                if self.faces > 0:
                    try:
                        for i in ids:
                            #print "EngZone: ", self.memory.getData("PeoplePerception/Person/"+str(i)+"/EngagementZone")
                            if self.memory.getData("PeoplePerception/Person/"+str(i)+"/EngagementZone") < 2:
                                self.gaze += self.memory.getData("PeoplePerception/Person/"+str(i)+"/IsLookingAtRobot")
                    except:
                        pass
                    self.people_name()
            return self.faces
    
    
    def people_name(self):
        self.name = '...'
        people = self.memory.getData("FaceDetection/FaceDetected")
        try:
            if people[0][5][0][1] > 0.45:
                self.name = people[0][5][0][0]
        except:
            pass
        return self.name


    def setState(self):
        cs='unknowState'
        if (self.faces==0) and (self.gaze==0):
            cs='searching4person'
        if (self.faces>0) and (self.gaze==0):
            cs='waiting4gaze'
        if (self.faces>0) and (self.gaze>0) and (self.name=='...'):
            cs='eng2unknow'
        if (self.faces>0) and (self.gaze>0) and (self.name!='...'):
            cs='eng2know'
        if (((self.currentState=='dialog') or (self.currentState=='eng2know')) and (self.gaze>0)) or (self.name!='...'):
            cs='dialog'
            
        return cs


if __name__ == "__main__":

    Robot_IP =  str(rospy.get_param('robot_ip'))
    Robot_Port = str(rospy.get_param('robot_port'))
    Robot_Name = str(rospy.get_param('robot_name'))

    rospy.init_node(Robot_Name + '_face_tracking', anonymous=True)
    face = rospy.Publisher(Robot_Name + '/face_tracking', Int8, queue_size=0)
    gaze = rospy.Publisher(Robot_Name + '/gaze_tracking', Int8, queue_size=0)
    face_name = rospy.Publisher(Robot_Name + '/face_name', String, queue_size=0)
    
    f = rospy.Publisher(Robot_Name + '/face_trackingStable', Int8, queue_size=0)
    g = rospy.Publisher(Robot_Name + '/gaze_trackingStable', Int8, queue_size=0)
    f_n = rospy.Publisher(Robot_Name + '/face_nameStable', String, queue_size=0)

    status = rospy.Publisher(Robot_Name + '/face_status', String, queue_size=0)
    
    rate = rospy.Rate(3) # Hz

    faceTracking = FaceTracking();
    faceTracking.gaze_tolerance = 0.4
    # default FirstLimitDistance is 1.5m (default SecondLimitDistance is 2.5m)
    faceTracking.engagement_zones.setFirstLimitDistance(1.3)
    nfaces = 0
    
    faceStableList = deque(faceS)
    gazeStableList = deque(gazeS)
    facenameStableList=deque(facenameS)
    

    try:
        while not rospy.is_shutdown():
            faces = faceTracking.detect()
            
            faceStableList.pop()
            faceStableList.appendleft(faceTracking.faces)
            faceStable=int(round(sum(faceStableList)/8.0))
                        
            gazeStableList.pop()
            gazeStableList.appendleft(faceTracking.gaze)
            gazeStable=int(round(sum(gazeStableList)/8.0))
                        
            facenameStableList.pop()
            facenameStableList.appendleft(faceTracking.name)
            X=Counter(facenameStableList).most_common()
            if(len(X)==1):
                face_nameStable=X[0][0]
            else:
                if (X[0][0]=='...'):
                    face_nameStable=X[1][0]
                                    
            face.publish(faceTracking.faces)
            gaze.publish(faceTracking.gaze)
            face_name.publish(face_nameStable)
            
            f.publish(faceStable)
            g.publish(gazeStable)
            f_n.publish(face_nameStable)
            #print "numero facce: " + str(faceTracking.faces), "Sguardo intercettato: "+str(faceTracking.gaze), "nome faccia: "+faceTracking.name    
            #print "numero facce S: " + str(faceStable), "Sguardo intercettato S: "+str(gazeStable), "nome faccia S: "+face_nameStable  
            #print str(faceTracking.faces)+";", str(faceStable)+";", str(faceTracking.gaze)+";", str(gazeStable)+";", faceTracking.name+";", face_nameStable

            faceTracking.faces = faceStable
            faceTracking.gaze = gazeStable
            faceTracking.name = face_nameStable
            
            faceTracking.currentState = faceTracking.setState()
            status.publish(faceTracking.currentState)
            
            #print faceTracking.currentState
            
            if (faces != nfaces):
                nfaces = faces
            rate.sleep()

            if faceTracking.tabShow == "True":
                tabletShowText(str(faceTracking.faces) + ") " + faceTracking.currentState + " : " + faceTracking.name)

    finally:
        if faceTracking.tabShow == "True":
            tabletShowText("")
        faceTracking.close()

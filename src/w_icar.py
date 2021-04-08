#! /usr/bin/env python
# -*- encoding: UTF-8 -*-

import os
import sys
import time
import qi
import smach
import smach_ros

import rospy
from std_msgs.msg import String, Int8
import urllib
import json
from pprint import pprint

from __builtin__ import True
sys.path.append(os.path.dirname(__file__) + "/../pyLib/")
from tablet import tabletShowPage
import robot_s2t as s2t

logger = qi.Logger("w-icar-node")

max_step = 3
state_timeout = 10
person = '...'
lastPerson = ''
currentState = 'unknowState'
gaze_found = False

session = ''
Robot_Name = ''
task_type = ''
task_drug = ''
task_timing = ''
control = ''
sentence = ''
reply = ''

animatedSpeechService = ''
soundsService = ''
behaviorService = ''
faceDetectionService = ''
ledService = ''
motionService = ''
postureService = ''
awarenessService = ''
commandURL = ''
tabletService = ''
tabletApp = ''
memoryService = ''


# Gaze ROS topic callback function
def gazeFound(data):
    global gaze_found
    if data.data > 0:
        gaze_found = True
    else:
        gaze_found = False


# Person name ROS topic callback function
def namePerson(data):
    global person
    person = data.data


# Face tracking status ROS topic callback function
def status(data):
    global currentState
    currentState = data.data


# Open session to SoftBank (Aldebaran) robot NAOqi
def connectRobot():
    global session, Robot_Name, Speech2Text, tabletApp
    Robot_IP =  rospy.get_param('robot_ip')
    Robot_Port = rospy.get_param('robot_port')
    Robot_Name = rospy.get_param('robot_name')
    
    session = qi.Session()
    
    try:
        connection_url = "tcp://" + Robot_IP + ":" + Robot_Port
        session.connect(connection_url)
        tabletApp = qi.Application(["PepperTablet", "--qi-url=" + connection_url])
        tabletApp.start()

    except RuntimeError:
        print ("Can't connect to Naoqi at ip " + Robot_IP + " on port " + Robot_Port + "\n Please check your script arguments. Run with -h option for help.")
        sys.exit(1)


# Activate NAOqi services connections
def activeServices():
    global session, animatedSpeechService, soundsService, behaviorService, faceDetectionService, ledService, motionService, postureService, awarenessService, tabletService, memoryService
    animatedSpeechService = session.service("ALAnimatedSpeech")
    motionService = session.service("ALMotion")
    postureService = session.service("ALRobotPosture")
    soundsService = session.service("ALAudioPlayer")
    behaviorService = session.service("ALBehaviorManager")
    memoryService = session.service("ALMemory")
    awarenessService = session.service('ALBasicAwareness')
    faceDetectionService = session.service("ALFaceDetection")
    tabletService = session.service("ALTabletService")
    ledService = session.service("ALLeds")
    s2t.AudioInit()    


# Activate ROS topics subscription
def topicsSubscription():
    global Robot_Name, control
    rospy.init_node(Robot_Name + '_w_icar', anonymous=True)
    rospy.Subscriber('/' + Robot_Name + '/gaze_tracking', Int8, gazeFound)
    rospy.Subscriber('/' + Robot_Name + '/face_nameStable', String, namePerson)
    rospy.Subscriber('/' + Robot_Name + '/face_status', String, status)


# Manages robot CrushesEyes behaviours
def crushesEyes(val):
    behaviorService.stopBehavior("schiacciaocchibianchi/behavior_1")
    behaviorService.stopBehavior("schiacciaocchiverdi/behavior_1")
    behaviorService.stopBehavior("schiacciaocchiblue/behavior_1")
    ledService.fadeRGB("FaceLeds",0x303030,0)
    if val == 'blue':
        behaviorService.runBehavior("schiacciaocchiblue/behavior_1", _async=True)
        return 0
    if val == 'verdi':
        behaviorService.runBehavior("schiacciaocchiverdi/behavior_1", _async=True)
        return 0
    if val == 'bianchi':
        behaviorService.runBehavior("schiacciaocchibianchi/behavior_1", _async=True)
        return 0
    if val == 'off':
        behaviorService.stopBehavior("schiacciaocchiblue/behavior_1", _async=True)
        behaviorService.stopBehavior("schiacciaocchiverdi/behavior_1", _async=True)
        behaviorService.stopBehavior("schiacciaocchibianchi/behavior_1", _async=True)
        return 0


# Enable robot internal motion modes
def activeMotionModes():
    motionService.setBreathEnabled('Body', True)
    motionService.setBreathEnabled('Head', True)


# Activate audio listening and convert it to text (google service)
def listen2text():
    global gaze_found, soundsService, state_timeout
    
    print "Listening..."
    text = ''
    locked = gaze_found # if True
    s2t.ON = False
    timeout = time.time() + state_timeout
    crushesEyes('verdi')
    tabletShowPage("dialog/eng2know.html")    
    while locked:
        s2t.ON = gaze_found
        # Stop listening if you look away before starting to speak   
        if not(s2t.ON) and not(s2t.rec):
            locked = False
            fileId = soundsService.loadFile("/opt/aldebaran/share/naoqi/wav/bip_gentle.wav")
            soundsService.play(fileId, _async=True)
            break
        # Keep recording active
        if s2t.ON and s2t.audioON():
            s2t.start = True
        else:
            s2t.start = s2t.audioON()
            timeout = time.time() + 5
        text = ''
        if (s2t.start is True) and (s2t.rec is False):
            s2t.rec = True
            tabletShowPage("dialog/recording.html")
            print "Recording..."
        if (s2t.start is False) and (s2t.rec is True):
            s2t.save_speech(s2t.FILENAME, s2t.preAudio+s2t.audio2send)
            s2t.rec = False
            print "End registration.\n"
            crushesEyes('off')
            tabletShowPage("dialog/Thinking.html")
            # Call Google Speack2Text service
            text = s2t.send2google(s2t.FILENAME, "it-IT").encode('utf-8')
            s2t.audio2send = []
            s2t.preAudio = []
            locked = False
        else:
            if time.time() > timeout:
                print "Listen timeout!"
                text = ''
                locked = False
    crushesEyes('off')
    tabletShowPage("dialog/void.html")        
    return text


# The robot speaks the "text" with the internal predefined service
def speech(text):
    global animatedSpeechService
    crushesEyes('blue')
    tabletShowPage("dialog/talking.html")
    animatedSpeechService.say(text)
    crushesEyes('off')
    tabletShowPage("dialog/void.html")
    return 0

# Wait for a human presence (ROS smach state)
class Wait(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes = ['human_presence','end'])
    def execute(self, ud):
        global currentState
        print "RUN Wait", currentState
        tabletShowPage("dialog/searching4person.html")
        locked = True
        while locked:
            if (currentState <> 'searching4person'):
                locked = False
                speech("Ciao!")
        return 'human_presence'


# Try to recognize the human present (ROS smach state)
class PersonDetected(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes = ['recognized','unrecognized','human_absence'],
                                   input_keys = ['state_timeout'])
    def execute(self, ud):
        global person, currentState
        print "RUN PersonDetected"
        locked = True
        say = True
        trans = 'unrecognized'
        timeout = time.time() + ud.state_timeout
        while locked:
            if (currentState == 'eng2know') or person <> '...':
                locked = False
                trans = 'recognized'
            if currentState == 'waiting4gaze':
                if say:
                    speech("Se vuoi parlare con me, avvicìnati e guardami negli occhi.")
                    say = False
            if currentState == 'eng2unknow':
                locked = False
                trans = 'unrecognized'
            if (time.time() > timeout):
                locked = False
                trans = 'human_absence'
                print "Recognition Timeout!", trans
        return trans


# Meet an unknown (ROS smach state)
class EngagedWithUnknown(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes = ['handshake','error'],
                                   input_keys = ['state_timeout'])
    def execute(self, ud):
        global currentState
        print "RUN EngagedWithUnknown"
        locked = True
        trans = 'error'
        timeout = time.time() + ud.state_timeout
        while locked:
            if currentState == 'eng2unknow':
                trans = 'handshake'
                locked = False                        
            if (time.time() > timeout):
                print "Recognition Timeout!", trans
                locked = False        
        return trans
    

# Meet someone you know and listen to them (ROS smach state)
class EngagedWithKnown(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes = ['listening','speaking','error'],
                                   input_keys = ['state_timeout'])
    def execute(self, ud):
        global currentState
        print "RUN EngagedWithKnown"
        locked = True
        trans = 'error'
        timeout = time.time() + ud.state_timeout
        while locked:
            if currentState == 'dialog':
                #speech("Dimmi pure...")
                trans = 'listening'
                locked = False
            if (time.time() > timeout):
                print "Recognition Timeout!", trans
                locked = False        
        return trans
    

# Activate a handshake with an unknown person (ROS smach state)
class Handshake(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes = ['eng2unknow','eng2know'],
                                   input_keys = ['lastPerson'],
                                   output_keys = ['lastPerson'])
    def execute(self, ud):
        global soundsService, faceDetectionService, behaviorService
        trans = 'eng2unknow'
        time.sleep(2)
        speech("Non credo di conoscerti.")
        time.sleep(1)
        speech("Qual'è il tuo nome?")
        time.sleep(1)

        text = ''
        ud.lastPerson = ''
        text = listen2text()
        name = ''
        # Check the name   
        while (text.strip() <> 'ok'):
            name = text
            if text <> '':
                speech("Ciao " + name + ". Se ho capito bene il tuo nome, dici OK! ... Altrimenti, ripeti il tuo nome!")
                text = ''
            text = listen2text()
            print "Handshake:", text
        # Face recognition         
        if (name <> ''):
            speech("Bene " + name + ", continua a guardarmi per qualche istante, affinché possa memorizzare il tuo volto...")
            print "Riconscimento..."
            # Call face recognition service
            faceDetectionService.setRecognitionEnabled(True)
            if faceDetectionService.learnFace(name):
                print "Riconosciuto!"
                behaviorService.runBehavior("animations/Stand/Waiting/TakePicture_1", _async=False)
                speech("Fatto. Adesso siamo amici...  Facciamo quattro chiacchiere.")
                ud.lastPerson = name
                trans = 'eng2know'            
            else:
                time.sleep(2)
                print "Riconoscimento fallito!"
                speech("Mi dispiace... Non ci sono riuscito.")
            name = ''
            fileId = soundsService.loadFile("/opt/aldebaran/share/naoqi/wav/end_reco.wav")
            soundsService.play(fileId, _async=True)
        print faceDetectionService.getRecognitionConfidenceThreshold(), faceDetectionService.getLearnedFacesList()    
        print "End handshake."
        return trans


# Activate a known person listening (ROS smach state)
class UserSpeaks(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes = ['done','error'],
                                   input_keys = ['sentence'],
                                   output_keys = ['sentence'])
    def execute(self, ud):
        ud.sentence = ''
        trans = 'error'
        print "RUN UserSpeaks"
        ud.sentence = listen2text()
        if (ud.sentence <> ''):
            trans = 'done'
        return trans

 
# Call the knowledge base service sending the person's sentence (ROS smach state)        
class RobotThinks(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes = ['done'],
                                   input_keys = ['sentence','reply'],
                                   output_keys = ['reply'])
    def execute(self, ud):
        tabletShowPage("dialog/Thinking.html")
        # Knowledge Base service
        # sentence = "Cosa devo fare oggi?"
        url_service = "http://deep.pa.icar.cnr.it:5042/reactive-dialog?text="+ud.sentence+"&patientId=115"
        try:
            print "\nQuery: ", url_service
            text_to_server = urllib.urlopen(url_service)
            reply_from_server = json.loads(text_to_server.read())
            # {"drug_info":
            #  {"dictionaire":"",
            #   "keyboard":false,
            #   "suggestions":[],
            #   "threshold":""},
            #  "event":"reactive-dialog",
            #  "event_status":"terminated",
            #  "rasa":"oggi non devi fare nulla",
            #  "status_request":
            #    {"code":200,
            #     "text":"success"}
            # }
            ud.reply = reply_from_server["rasa"]
            print "\nReply: ", ud.reply
        except:
            print "Connection error!"
            ud.reply = "Errore di connessione!"
        return 'done'


# The robot says the answer sentence of the knowledge base (ROS smach state)
class RobotReplies(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes = ['done'],
                                   input_keys = ['reply'])
    def execute(self, ud):
        print "RUN RobotReplies"
        speech(ud.reply)
        return 'done'


# The robot says the sentence (ROS smach state)
class RobotSpeaks(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes = ['done'],
                                   input_keys = ['sentence'])
    def execute(self, ud):
        print "RUN RobotSpeaks"
        speech(ud.sentence)
        return 'done'


def main():
    connectRobot()
    activeServices()
    global Robot_Name, faceDetectionService, currentState, person, state_timeout, sentence, lastPerson, reply
    Robot_Name = rospy.get_param('robot_name')
    topicsSubscription()
    logger.info("W-ICAR Node started")

    faceDetectionService.clearDatabase()
    time.sleep(2)

    # Create a SMACH state machine
    sm_top = smach.StateMachine(outcomes=['stop'])
    sm_top.userdata.state_timeout=state_timeout
    sm_top.userdata.sentence=sentence
    sm_top.userdata.lastPerson=lastPerson
    sm_top.userdata.reply=reply
    
    # Open the container
    with sm_top:
        smach.StateMachine.add('Wait', Wait(), transitions={'human_presence':'PersonDetected','end':'stop'})
        smach.StateMachine.add('PersonDetected', PersonDetected(), transitions={'recognized':'EngagedWithKnown','unrecognized':'EngagedWithUnknown','human_absence':'Wait'})
        smach.StateMachine.add('EngagedWithKnown', EngagedWithKnown(), transitions={'listening':'UserSpeaks','speaking':'RobotSpeaks','error':'PersonDetected'})        
        smach.StateMachine.add('EngagedWithUnknown', EngagedWithUnknown(), transitions={'handshake':'Handshake','error':'PersonDetected'})
        smach.StateMachine.add('UserSpeaks', UserSpeaks(), transitions={'done':'RobotThinks','error':'EngagedWithKnown'})
        smach.StateMachine.add('RobotSpeaks', RobotSpeaks(), transitions={'done':'EngagedWithKnown'})
        smach.StateMachine.add('Handshake', Handshake(), transitions={'eng2know':'EngagedWithKnown','eng2unknow':'EngagedWithUnknown'})
        smach.StateMachine.add('RobotThinks', RobotThinks(), transitions={'done':'RobotReplies'})
        smach.StateMachine.add('RobotReplies', RobotReplies(), transitions={'done':'EngagedWithKnown'})

    # Create and start the introspection server
    sis = smach_ros.IntrospectionServer('sis_run', sm_top, '/W@ICAR')
    sis.start()

    # Execute SMACH plan
    outcome = sm_top.execute()

    # Wait for ctrl-c to stop the application
    sis.stop()


if __name__ == '__main__':
    main()

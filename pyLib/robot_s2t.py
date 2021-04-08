#! /usr/bin/env python
# -*- encoding: UTF-8 -*-

import sys
import qi
import time

import rospy
from naoqi_bridge_msgs.msg import AudioBuffer
import wave
import struct
import speech_recognition as sr

PREV_SIZE = 16  # Numbers of frames before speech
FORMAT = 2      # 2 bytes = 16 bit
CHANNELS = 2
RATE = 24000
THRESHOLD = 2400   # The threshold intensity that defines silence
                   # and noise signal (an int. lower than THRESHOLD is silence).

SILENCE_LIMIT = 1  # Silence limit in seconds. The max ammount of seconds where
                   # only silence is recorded. When this time passes the
                   # recording finishes and the file is delivered.

FILENAME = '/tmp/robot-s2t-rec.wav'

ON = False
audio2send = []
preAudio = []
rec = False

session = ''
Robot_Name = ''

audioService = ''
soundsService = ''

gcloud_credential = ''


def AudioInit():
    global Robot_Name
    
    connectRobot()
    activeServices() 
    rospy.Subscriber('/' + Robot_Name + '/naoqi_driver/audio', AudioBuffer, audioback) #audio input


def connectRobot():
    global session, Robot_Name  
    Robot_IP =  rospy.get_param('robot_ip')
    Robot_Port = rospy.get_param('robot_port')
    Robot_Name = rospy.get_param('robot_name')
    session = qi.Session()
    
    try:
        session.connect("tcp://" + Robot_IP + ":" + Robot_Port)
    except RuntimeError:
        print ("Can't connect to Naoqi at ip " + Robot_IP + " on port " + Robot_Port + "\n Please check your script arguments. Run with -h option for help.")
        sys.exit(1)


def activeServices():
    global session, audioService, soundsService
    audioService = session.service("ALAudioDevice")
    soundsService = session.service("ALAudioPlayer")


def audioON():
    global audioService, THRESHOLD, SILENCE_LIMIT
    try:
        if audioService.getFrontMicEnergy() > THRESHOLD:
            return True
        else:
            tnow = time.time()
            c = 0
            while (time.time() - tnow) < SILENCE_LIMIT:
                if audioService.getFrontMicEnergy() > THRESHOLD:
                    c = 1
            if c > 0:
                return True
            else:
                return False
    except Exception, e:
        print "Error was:", e


# Saves mic data to temporary WAV file.
# writes data to WAV file
def save_speech(filename, data):
    data = ''.join(data)
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(FORMAT)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()
    

def send2google(filename, lang):
    global gcloud_credential
    testo = ''
    r = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = r.record(source)
        
    r.operation_timeout = 15
    try:
        testo = r.recognize_google(audio, language=lang)
    except sr.UnknownValueError:
        print "Non ho capito."
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))
    
    return testo


def audioback(data):
    global audio2send, preAudio, rec
    mem = []
    
    try:
        mem = data.data[0:len(data.data):8]
    except:
        pass
    if (rec is True):
        #print "REC", len(audio2send)
        audio2send.append(struct.pack('%si' % len(mem), *mem))
    else:
        if len(preAudio) == PREV_SIZE:
            del preAudio[0]
        preAudio.append(struct.pack('%si' % len(mem), *mem))


if __name__ == "__main__":
    AudioInit()

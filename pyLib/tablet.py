#! /usr/bin/env python
# -*- encoding: UTF-8 -*-

import qi
import sys
import time
import rospy

Nao_IP = 'pepper'


def tabletShowText(text):
    session = qi.Session()
    
    try:
        session.connect("tcp://" + Nao_IP + ":9559")
    except RuntimeError:
        print ("Can't connect to Naoqi at " + Nao_IP + " on port 9559\nPlease check your script arguments. Run with -h option for help.")
        sys.exit(1)

    # Get the service ALTabletService.
    tabletService = session.service("ALTabletService")
    tabletService.loadApplication("j-tablet-browser")
    tabletService.showWebview()
    
    try:
        tabletService.showWebview("http://198.18.0.1/apps/crss_tablet/tabtext.html")

        time.sleep(1)

        stringa = '"' + text + '"'
        if len(text.split()) < 20:
            script = """
              var x = document.getElementById("ttsDivNoScroll");
              x.style.display = "inline";          
              document.getElementById("contentNoScroll").innerHTML = """ + stringa + """;
            """
        else:
            script = """
              var x = document.getElementById("ttsDivScroll");
              x.style.display = "inline";          
              document.getElementById("contentScroll").innerHTML = """ + stringa + """;
            """
        #print(script)
        tabletService.executeJS(script)

        # inject and execute the javascript in the current web page displayed
        #tabletService.executeJS(script)

    except Exception, e:
        print "Error was:", e

    # Hide the web view
    #tabletService.hideWebview()


def tabletShowPage(page):
    session = qi.Session()
    
    try:
        session.connect("tcp://" + Nao_IP + ":9559")
    except RuntimeError:
        print ("Can't connect to Naoqi at ip " + Nao_IP + " on port 9559\nPlease check your script arguments. Run with -h option for help.")
        sys.exit(1)

    # Get the service ALTabletService.
    tabletService = session.service("ALTabletService")
    tabletService.loadApplication("j-tablet-browser")
    tabletService.showWebview()

    try:
        tabletService.showWebview("http://198.18.0.1/apps/crss_tablet/"+page)

    except Exception, e:
        print "Error was:", e

    # Hide the web view
    #tabletService.hideWebview()


if __name__ == "__main__":
    
    tabletShowText("Please check your script arguments.")

# w@icar
This project (ROS Package) implements a model based on bidirectional multi-modal signs of checking human-robot engagement and interaction.

# Prerequisites:
- NAO or Pepper Robot (https://www.softbankrobotics.com/)
- Choreograph (https://www.softbankrobotics.com/emea/en/support/)
- ROS (https://www.ros.org/) (rosdistro: kinetic)
- NAOqi (http://doc.aldebaran.com/index.html) 
- Python 2.7
- rospy (http://wiki.ros.org/rospy)
- pepper-bringup (http://wiki.ros.org/pepper)
- nao-bringup (http://wiki.ros.org/nao)

# Installation:
- Clone GitHub repository into src directory of your ROS workspace 
(git clone https://github.com/hri-cnr-lab/w_icar.git)
- Execute catkin_make on the root of your ROS workspace
- Install in the robot all behaviours with Choreograph from src/w_icar/behaviours

# Configuration:
Set your parameters in src/w_icar/launch/engagement.launch 
- robot_ip [IP of the robot] (Default: from "pepper" name on DNS or in file /etc/hosts)
- robot_port [NAOqi proxy port] (Default: from environment variable NAO_PORT  or the 9559 value)
- robot_name [The robot name] (Default: "pepper")
- engMode [The engagement mode] ("Unengaged", “FullyEngaged“, “SemiEngaged“. Default: "FullyEngaged")
- trackMode [The tracking mode] (“Head“, “BodyRotation“, “WholeBody“, “MoveContextually“. Default: "BodyRotation")

# Execution:
- Launch the roscore
- Launch pepper bringup 
(roslaunch pepper_bringup pepper_full.launch nao_ip:=<robot_ip> namespace:=<robot_name>)
- Launch w_icar engagement 
(roslaunch  w_icar engagement.launch)
- Launch w_icar w_icar 
(roslaunch w_icar w_icar.launch)




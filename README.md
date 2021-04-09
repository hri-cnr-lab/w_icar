# w@icar
This project (ROS Package) implements a model based on bidirectional multi-modal signs of checking human-robot engagement and interaction.

# Prerequisites:
- NAO or Pepper Robot (https://www.softbankrobotics.com/)
- ROS (https://www.ros.org/) (rosdistro: kinetic)
- NAOqi (http://doc.aldebaran.com/index.html) 
- Python 2.7
- rospy (http://wiki.ros.org/rospy)
- pepper-bringup (http://wiki.ros.org/pepper)
- nao-bringup (http://wiki.ros.org/nao)

# Installation and execution:
- Clone GitHub repository into src directory of your ROS workspace
	(git clone https://github.com/hri-cnr-lab/w_icar.git)
- Execute catkin_make on the root of your ROS workspace
- Launch the roscore
- Launch pepper bringup (roslaunch pepper_bringup pepper_full.launch nao_ip:=<robot_ip> namespace:=pepper)
- Launch w_icar engagement (roslaunch  w_icar engagement.launch)
- Launch w_icar w_icar (roslaunch w_icar w_icar.launch)




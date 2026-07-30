#  Copyright 2020 Unity Technologies
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import rclpy
import socket
import re

from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSReliabilityPolicy
from rclpy.qos import QoSProfile

from .communication import RosReceiver


class RosSubscriber(RosReceiver):
    """
    Class to send messages outside of ROS network
    """

    def __init__(self, topic, message_class, tcp_server, queue_size=10):
        """

        Args:
            topic:         Topic name to publish messages to
            message_class: The message class in catkin workspace
            queue_size:    Max number of entries to maintain in an outgoing queue
        """
        strippedTopic = re.sub("[^A-Za-z0-9_]+", "", topic)
        self.node_name = f"{strippedTopic}_RosSubscriber"
        RosReceiver.__init__(self, self.node_name)
        self.topic = topic
        self.msg = message_class
        self.tcp_server = tcp_server
        self.queue_size = queue_size

        qos_profile = QoSProfile(depth=queue_size)
        qos_profile.reliability = self._resolve_reliability()

        # Start Subscriber listener function
        self.subscription = self.create_subscription(
            self.msg, self.topic, self.send, qos_profile  # queue_size
        )
        self.subscription

    def _resolve_reliability(self):
        """Pick a reliability policy that matches whoever is publishing this topic.

        A RELIABLE subscription does not match a BEST_EFFORT publisher, so the
        subscription would silently receive nothing. Rather than guessing from
        the message type, ask the graph what the current publishers advertise
        and mirror it. BEST_EFFORT wins if any publisher is best-effort, since
        that is the only policy compatible with all of them.

        Falls back to a message-type heuristic when no publisher has appeared
        yet -- Unity often subscribes before the camera driver has started.
        """
        try:
            publishers = self.get_publishers_info_by_topic(self.topic)
        except (NotImplementedError, ValueError):
            publishers = []

        if publishers:
            if any(
                p.qos_profile.reliability == QoSReliabilityPolicy.BEST_EFFORT
                for p in publishers
            ):
                return QoSReliabilityPolicy.BEST_EFFORT
            return QoSReliabilityPolicy.RELIABLE

        # No publisher yet: sensor streams are best-effort far more often than
        # not, so default those to BEST_EFFORT and everything else to RELIABLE.
        if self.msg.__name__ in ("Image", "CompressedImage", "PointCloud2", "LaserScan"):
            return QoSReliabilityPolicy.BEST_EFFORT
        return QoSReliabilityPolicy.RELIABLE

    def send(self, data):
        """
        Connect to TCP endpoint on client and pass along message
        Args:
            data: message data to send outside of ROS network

        Returns:
            self.msg: The deserialize message

        """
        self.tcp_server.send_unity_message(self.topic, data)
        return self.msg

    def unregister(self):
        """

        Returns:

        """
        self.destroy_subscription(self.subscription)
        self.destroy_node()

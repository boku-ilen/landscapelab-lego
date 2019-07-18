# NOTE since this script is executed in the QGIS-Python environment
#  PyCharm might wrongfully mark some libraries/classes as unknown
import os
import socket
from qgis.core import *
from qgis.utils import *
from UtilityFunctions import render_image
import config

"""
NOTE: in order for this script to work, the QGIS plugin PowerPan has to be installed

To run this make sure that the path to this file is included in sys.path
then call 'import QGIS_POC1' in the QGIS pyton console
"""


class RemoteRendering(QgsTask):

    def __init__(self):
        super().__init__('remote control listener task', QgsTask.CanCancel)

        QgsMessageLog.logMessage('setting up RemoteRendering Task')

        # define image path
        self.image_location = os.path.join(QgsProject.instance().homePath(), 'outputImage.png')

        # setup UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((config.QGIS_IP, config.QGIS_READ_PORT))
        self.write_target = (config.QGIS_IP, config.LEGO_READ_PORT)

    # listens on socket for commands and
    def run(self):

        try:
            QgsMessageLog.logMessage('starting to listen for messages')
            while True:
                # wait for msg
                data, addr = self.socket.recvfrom(config.UDP_BUFFER_SIZE)
                data = data.decode()
                QgsMessageLog.logMessage('got message {} from address {}'.format(data, addr))

                # if msg is exit stop
                if data == 'exit':
                    self.socket.sendto(b'exit', self.write_target)
                    QgsMessageLog.logMessage('stop listening')
                    return True

                if data.startswith(config.RENDER_KEYWORD):
                    extent_info = data[len(config.RENDER_KEYWORD):]
                    extent = extent_info.split(' ')

                    extent = QgsRectangle(float(extent[0]), float(extent[1]), float(extent[2]), float(extent[3]))

                    render_image(extent, self.image_location)
                    self.socket.sendto(
                        '{}{}'.format(config.UPDATE_KEYWORD, extent_info).encode(),
                        self.write_target
                    )

        finally:
            self.socket.close()


def start_remote_rendering_task():
    remote_render_task = RemoteRendering()
    QgsApplication.taskManager().addTask(remote_render_task)

    return remote_render_task
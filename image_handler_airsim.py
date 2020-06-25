import airsim
import numpy as np
import os
import behavior
import behavior3
import behavior2
import behavior4
import resources
import datetime
import yolo


class AirsimHandler:

    def __init__(self):
        # connect to the AirSim simulator
        self.client = airsim.CarClient()
        self.client.enableApiControl(True)

    def evaluate_all_tasks(self, yoloclient=yolo.YOLO()):

        behavior2.location(self.client)
        while not self.client.confirmConnection():
            responses = self.load_images()
            for response in responses:
                now = datetime.datetime.now()
                date_time = now.strftime("%d-%m-%Y,%H-%M-%S-%f")
                if not os.path.exists(resources.filename):
                    os.makedirs(resources.filename)

                print("Detect objects")
                image = np.fromstring(response.image_data_uint8, dtype=np.uint8)  # get numpy array
                # reshape array to 4 channel image array H X W X 4
                img_rgba = image.reshape(response.height, response.width, 4)
                img_rgb = rgba2rgb(img_rgba)
                img_dist_topleftp = yoloclient.detect_image(img_rgb)
                image_result = img_dist_topleftp[0]
                image_result.save(resources.filename + date_time + ".png")
                behavior2.drive(self.client, airsim.CarControls(),
                                         img_dist_topleftp[1], img_dist_topleftp[2])
        yoloclient.close_session()
        self.client.reset()

# self.client.simPrintLogMessage("Print on screen") print on application screen

    def load_images(self):
        # scene vision image in uncompressed RGBA array
        responses = self.client.simGetImages([
            airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)])
        print("Got the image!")
        return responses

    def get_state_position(self):
        return self.client.getCarState().kinematics_estimated.position


def rgba2rgb(rgba, background=(255, 255, 255)):
    row, col, ch = rgba.shape

    if ch == 3:
        return rgba
    assert ch == 4, 'RGBA image has 4 channels.'

    rgb = np.zeros((row, col, 3), dtype='float32')
    r, g, b, a = rgba[:, :, 0], rgba[:, :, 1], rgba[:, :, 2], rgba[:, :, 3]

    a = np.asarray(a, dtype='float32') / 255.0

    R, G, B = background

    rgb[:, :, 0] = r * a + (1.0 - a) * R
    rgb[:, :, 1] = g * a + (1.0 - a) * G
    rgb[:, :, 2] = b * a + (1.0 - a) * B

    return np.asarray(rgb, dtype='uint8')

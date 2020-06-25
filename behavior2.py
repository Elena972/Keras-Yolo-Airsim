import airsim
import time
import numpy as np
import resources


def location(client):
    return client.simSetVehiclePose(
        airsim.Pose(airsim.Vector3r(x_val=60.330116271972656, y_val=-272.38421630859375, z_val=-0.6507290601730347),
                    airsim.Quaternionr(w_val=0.7091798782348633, x_val=4.51675005024299e-05,
                                       y_val=-2.079392288578674e-06, z_val=0.7050275802612305)), True)


def drive(client, car_controls, distance, top_point_of_object):
    time.sleep(0.5)
    distance = np.array(distance)
    top_point_of_object = np.array(top_point_of_object)
    x_car_in_move = client.getCarState().kinematics_estimated.position.x_val
    time.sleep(0.01)

    if np.any(top_point_of_object > resources.TH_left_point_obj) and np.any(distance < resources.TH_distance):
        # apply brakes
        car_controls.brake = 1
        client.setCarControls(car_controls)
        print("Frana!", top_point_of_object, distance)
        time.sleep(1.5)  # let car drive a bit
        car_controls.brake = 0  # remove brake
        #client.simPrintLogMessage("Regim de franare pentru evitarea coliziunii!", "345", 3)
        time.sleep(0.5)

    elif resources.right_line2 < x_car_in_move < resources.left_line2 and np.any(distance > resources.TH_distance) \
            or (np.all(distance == 0.) and np.all(top_point_of_object == 0.)):
        # go forward
        car_controls.throttle = 0.6
        car_controls.steering = 0
        client.setCarControls(car_controls)
        print("Inainte", top_point_of_object, distance)
        time.sleep(0.5)

    elif x_car_in_move < resources.right_line2 and np.any(distance > resources.TH_distance):
        # Go forward + steer left
        car_controls.throttle = 0.4
        car_controls.steering = -0.01
        client.setCarControls(car_controls)
        print("Viraj stanga", top_point_of_object, distance)
        time.sleep(0.5)

    elif x_car_in_move > resources.left_line2 and np.any(distance > resources.TH_distance):
        # Go forward + steer right
        car_controls.throttle = 0.4
        car_controls.steering = 0.01
        client.setCarControls(car_controls)
        print("Viraj dreapta", top_point_of_object, distance)
        time.sleep(0.5)

    else:
        if resources.TH_distance < np.all(distance) < 7.5:
            print("Inainte din inertie", top_point_of_object, distance)

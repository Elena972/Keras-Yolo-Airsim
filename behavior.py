import airsim
import time
import numpy as np
import resources


def location(client):
    return client.simSetVehiclePose(airsim.Pose(airsim.Vector3r(x_val=resources.x_location, y_val=resources.y_location,
                                                                z_val=resources.z_location),
                                    airsim.Quaternionr(w_val=resources.w_orientation, x_val=resources.x_orientation,
                                                       y_val=resources.y_orientation, z_val=resources.z_orientation)),
                                    True)


def drive_straight(client, car_controls, distance, top_point_of_object):
    time.sleep(0.5)
    distance = np.array(distance)
    top_point_of_object = np.array(top_point_of_object)
    x_car_in_move = client.getCarState().kinematics_estimated.position.x_val
    time.sleep(0.01)

    if np.any(top_point_of_object > resources.TH_left_point_obj) and np.any(distance < resources.TH_distance):
        # apply brakes
        car_controls.brake = 0.4
        client.setCarControls(car_controls)
        print("Frana!", top_point_of_object, distance)
        time.sleep(1)  # let car drive a bit
        car_controls.brake = 0  # remove brake
        #client.simPrintLogMessage("Regim de franare pentru evitarea coliziunii!", "345", 3)
        time.sleep(1)

    elif resources.right_line < x_car_in_move < resources.left_line and np.any(distance > resources.TH_distance) \
            or (np.all(distance == 0.) and np.all(top_point_of_object == 0.)):
        # go forward
        car_controls.throttle = 0.4
        car_controls.steering = 0
        client.setCarControls(car_controls)
        print("Inainte", top_point_of_object, distance)
        time.sleep(0.5)

    elif x_car_in_move <= resources.right_line and np.any(distance > resources.TH_distance):
        # Go forward + steer left
        car_controls.throttle = 0.4
        car_controls.steering = -0.01
        client.setCarControls(car_controls)
        print("Viraj stanga", top_point_of_object, distance)
        time.sleep(1)

    elif x_car_in_move >= resources.left_line and np.any(distance > resources.TH_distance):
        # Go forward + steer right
        car_controls.throttle = 0.4
        car_controls.steering = 0.01
        client.setCarControls(car_controls)
        print("Viraj dreapta", top_point_of_object, distance)
        time.sleep(1)

    else:
        if 7.2 < np.all(distance) < 7.5:
            print("Inainte din inertie", top_point_of_object, distance)

# -*- coding: utf-8 -*-
"""
Class definition of YOLO_v3 style detection model on image
Definition for mAP evaluation
"""
import numpy as np
import resources
import os
import colorsys
from math import sqrt
from timeit import default_timer as timer
from keras import backend as K
from keras.models import load_model
from keras.layers import Input
from PIL import Image, ImageFont, ImageDraw
from yolo3.model import yolo_eval, yolo_body, tiny_yolo_body
from yolo3.evaluate import normalize, evaluate
from yolo3.utils import letterbox_image
from yolo3.voc import parse_voc_annotation
from generator import BatchGenerator
from keras.utils import multi_gpu_model

class YOLO(object):
    _defaults = {
        "model_path": 'model_data/trained_weights_srv_1.h5',
        "anchors_path": 'model_data/yolo_anchors.txt',
        "classes_path": '2_classes.txt',
        "score" : 0.3,
        "iou" : 0.5,
        "model_image_size" : (416, 416),
        "gpu_num" : 0,
    }

    @classmethod
    def get_defaults(cls, n):
        if n in cls._defaults:
            return cls._defaults[n]
        else:
            return "Unrecognized attribute name '" + n + "'"

    def __init__(self, **kwargs):
        self.__dict__.update(self._defaults)  # set up default values
        self.__dict__.update(kwargs) # and update with user overrides
        self.class_names = self._get_class()
        self.anchors = self._get_anchors()
        self.sess = K.get_session()
        self.boxes, self.scores, self.classes = self.generate()

    def _get_class(self):
        classes_path = os.path.expanduser(self.classes_path)
        with open(classes_path) as f:
            class_names = f.readlines()
        class_names = [c.strip() for c in class_names]
        return class_names

    def _get_anchors(self):
        anchors_path = os.path.expanduser(self.anchors_path)
        with open(anchors_path) as f:
            anchors = f.readline()
        anchors = [float(x) for x in anchors.split(',')]
        return np.array(anchors).reshape(-1, 2)

    def generate(self):
        model_path = os.path.expanduser(self.model_path)
        assert model_path.endswith('.h5'), 'Keras model or weights must be a .h5 file.'

        # Load model, or construct model and load weights.
        num_anchors = len(self.anchors)
        num_classes = len(self.class_names)
        is_tiny_version = num_anchors==6 # default setting
        try:
            self.yolo_model = load_model(model_path, compile=False)
        except:
            self.yolo_model = tiny_yolo_body(Input(shape=(None,None,3)), num_anchors//2, num_classes) \
                if is_tiny_version else yolo_body(Input(shape=(None,None,3)), num_anchors//3, num_classes)
            self.yolo_model.load_weights(self.model_path) # make sure model, anchors and classes match
        else:
            assert self.yolo_model.layers[-1].output_shape[-1] == \
                num_anchors/len(self.yolo_model.output) * (num_classes + 5), \
                'Mismatch between model and given anchor and class sizes'

        print('{} model, anchors, and classes loaded.'.format(model_path))

        # Generate colors for drawing bounding boxes.
        hsv_tuples = [(x / len(self.class_names), 1., 1.)
                      for x in range(len(self.class_names))]
        self.colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
        self.colors = list(
            map(lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)),
                self.colors))
        np.random.seed(10101)  # Fixed seed for consistent colors across runs.
        np.random.shuffle(self.colors)  # Shuffle colors to decorrelate adjacent classes.
        np.random.seed(None)  # Reset seed to default.

        # Generate output tensor targets for filtered bounding boxes.
        self.input_image_shape = K.placeholder(shape=(2, ))
        if self.gpu_num>=2:
            self.yolo_model = multi_gpu_model(self.yolo_model, gpus=self.gpu_num)
        boxes, scores, classes = yolo_eval(self.yolo_model.output, self.anchors,
                len(self.class_names), self.input_image_shape,
                score_threshold=self.score, iou_threshold=self.iou)
        return boxes, scores, classes

    def detect_image(self, imagec):
        start = timer()
        distance = []
        left_point = []

        image = Image.fromarray(imagec.astype('uint8'), 'RGB')
        if self.model_image_size != (None, None):
            assert self.model_image_size[0]%32 == 0, 'Multiples of 32 required'
            assert self.model_image_size[1]%32 == 0, 'Multiples of 32 required'
            boxed_image = letterbox_image(image, tuple(reversed(self.model_image_size)))
        else:
            new_image_size = (image.width - (image.width % 32),
                              image.height - (image.height % 32))
            boxed_image = letterbox_image(image, new_image_size)
        image_data = np.array(boxed_image, dtype='float32')

        # print(image_data.shape)
        image_data /= 255.
        image_data = np.expand_dims(image_data, 0)  # Add batch dimension.

        out_boxes, out_scores, out_classes = self.sess.run(
            [self.boxes, self.scores, self.classes],
            feed_dict={
                self.yolo_model.input: image_data,
                self.input_image_shape: [image.size[1], image.size[0]],
                K.learning_phase(): 0
            })

        # print('Found {} boxes for {}'.format(len(out_boxes), 'img'))

        font = ImageFont.truetype(font='font/FiraMono-Medium.otf',
                    size=np.floor(3e-2 * image.size[1] + 0.5).astype('int32'))
        thickness = (image.size[0] + image.size[1]) // 300

        for i, c in reversed(list(enumerate(out_classes))):
            predicted_class = self.class_names[c]
            box = out_boxes[i]
            score = out_scores[i]

            label = '{} {:.2f}'.format(predicted_class, score)
            draw = ImageDraw.Draw(image)
            label_size = draw.textsize(label, font)
            # print(label, (left, top), (right, bottom))

            # box coordinates: x_min = left, y_min = top, x_max = right, y_max = bottom
            top, left, bottom, right = box
            top = max(0, np.floor(top + 0.5).astype('int32'))
            left = max(0, np.floor(left + 0.5).astype('int32'))
            bottom = min(image.size[1], np.floor(bottom + 0.5).astype('int32'))
            right = min(image.size[0], np.floor(right + 0.5).astype('int32'))

            # get the middle X coordinate of the box
            x_center = (left + right) / 2

            x_img = image.size[0] / 2
            y_img = image.size[1]

            # distance
            distance_car_object = float("{:.2f}".format(sqrt((x_center - x_img)**2 + (bottom - y_img)**2)*0.026))
            distance.append(distance_car_object)
            left_point.append(left)

            #print("The distance between car model and ", label, "is: ", distance, "meters")

            if top - label_size[1] >= 0:
                text_origin = np.array([left, top - label_size[1]])
            else:
                text_origin = np.array([left, top + 1])

            # apply non-max suppression
            #indices = cv2.dnn.NMSBoxes(box, score, 0.3, 0.25)

            # My kingdom for a good redistributable image drawing library.
            for i in range(thickness):
                draw.rectangle(
                    [left + i, top + i, right - i, bottom - i],
                    outline=self.colors[c])
            draw.rectangle(
                [tuple(text_origin), tuple(text_origin + label_size)],
                fill=self.colors[c])
            draw.text(text_origin, label, fill=(0, 0, 0), font=font)
            if distance_car_object < resources.TH_distance:
                draw.line([(x_center, bottom), (x_img, y_img)], fill=(255, 0, 0))
                draw.text([(x_center + x_img)/2, (bottom + y_img)/2], str(distance_car_object)+" m",
                          fill=(255, 0, 0), font=font)
            else:
                draw.line([(x_center, bottom), (x_img, y_img)], fill=self.colors[c])
                draw.text([(x_center + x_img) / 2, (bottom + y_img) / 2], str(distance_car_object) + " m",
                          fill=self.colors[c], font=font)

            del draw

        end = timer()
        print("Time for detection: " "%.2f" % (end - start), "sec")
        result = image, distance, left_point
        return result

    def calculateMap(self, config):
        ###############################
        #   Create the validation generator
        ###############################
        valid_ints, labels = parse_voc_annotation(
            config['valid']['valid_annot_folder'],
            config['valid']['valid_image_folder'],
            config['valid']['cache_name'],
            config['model']['labels']
        )

        labels = labels.keys() if len(config['model']['labels']) == 0 else config['model']['labels']
        labels = sorted(labels)

        valid_generator = BatchGenerator(
            instances=valid_ints,
            anchors=config['model']['anchors'],
            labels=labels,
            downsample=32,  # ratio between network input's size and network output's size, 32 for YOLOv3
            max_box_per_image=0,
            batch_size=config['train']['batch_size'],
            min_net_size=config['model']['min_input_size'],
            max_net_size=config['model']['max_input_size'],
            shuffle=True,
            jitter=0.0,
            norm=normalize
        )

        ###############################
        #   Load the model and do evaluation
        ###############################
        os.environ['CUDA_VISIBLE_DEVICES'] = config['train']['gpus']

        #infer_model = load_model(config['train']['saved_weights_name'])
        infer_model = yolo_body(Input(shape=(None, None, 3)), len(self.anchors) // 3, len(self.class_names))
        infer_model.load_weights("D:/PyCharm/PycharmProjects/keras-yolo3-airsim/model_data/trained_weights_srv_1.h5")  # make sure model, anchors and classes match


        # compute mAP for all the classes
        average_precisions = evaluate(infer_model, valid_generator)

        # print the score
        for label, average_precision in average_precisions.items():
            print(labels[label] + ': {:.4f}'.format(average_precision))
        print('mAP: {:.4f}'.format(sum(average_precisions.values()) / len(average_precisions)))

    def close_session(self):
        self.sess.close()

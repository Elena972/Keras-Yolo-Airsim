import argparse
import json
import yolo


def _main_(args):
   config_path = args.conf

   with open(config_path) as config_buffer:
        config = json.loads(config_buffer.read())
        yoloclient=yolo.YOLO()
        yoloclient.calculateMap(config)

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='Evaluate YOLO_v3 model on any dataset')
    argparser.add_argument('-c', '--conf', help='path to configuration file')

    args = argparser.parse_args()
    _main_(args)

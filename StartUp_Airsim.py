import image_handler_airsim


def main():

    image = image_handler_airsim.AirsimHandler()
    image.evaluate_all_tasks()


if __name__ == "__main__":
    main()

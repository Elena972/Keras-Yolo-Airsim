import sys
import keras
import matplotlib.pyplot as plt
import numpy as np

if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")


class TrainingHistoryPlot(keras.callbacks.Callback):
    def __init__(self):
        self.losses = []
        self.val_losses = []

    def on_train_begin(self, logs={}):
        self.losses = []
        self.val_losses = []

    def on_train_end(self, logs={}):
        nr = len(self.losses)
        n = np.arange(0, nr)

        plt.rc('font', family='Arial', size=10)

        plt.style.use("default")
        plt.figure()
        plt.title("Training history ")
        plt.xlabel("Epoch ")
        plt.ylabel("Loss")

        plt.plot(n, self.losses, label="loss")
        plt.plot(n, self.val_losses, label="val_loss")
        plt.legend()

        plt.savefig('output/Training-{}.png')
        plt.close()

    def on_epoch_end(self, epoch, logs={}):
        self.losses.append(logs.get('loss'))
        self.val_losses.append(logs.get('val_loss'))

        # Before plotting ensure at least 2 epochs have passed
        if len(self.losses) > 1:
            N = np.arange(0, len(self.losses))


            # Plot train loss, train acc, val loss and val acc against epochs passed
            plt.rc('font', family='Arial', size=10)
            plt.style.use("default")
            plt.figure()
            plt.plot(N, self.losses, label="train_loss")
            plt.plot(N, self.val_losses, label="val_loss")
            plt.title("Training Loss [Epoch {}]".format(epoch))
            plt.xlabel("Epoch ")
            plt.ylabel("Loss")
            plt.legend()
            # Make sure there exists a folder called output in the current directory
            # or replace 'output' with whatever direcory you want to put in the plots
            plt.savefig('output/Epoch-{}.png'.format(epoch))
            plt.close()

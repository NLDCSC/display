import logging

import cv2
import numpy as np
from nldcsc.loggers.app_logger import AppLogger
from skimage.metrics import structural_similarity as ssim

logging.setLoggerClass(AppLogger)


class CompareScreenshots(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def mse(self, imageA, imageB):
        """
        The 'Mean Squared Error' between the two images is the sum of the squared difference between the two images;

        NOTE: the two images must have the same dimension

        :param imageA: cv2.imread representation of image
        :type imageA: numpy.ndarray
        :param imageB: cv2.imread representation of image
        :type imageB: numpy.ndarray
        :return: return the MSE, the lower the error, the more "similar" the two images are
        :rtype: float
        """

        err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
        err /= float(imageA.shape[0] * imageA.shape[1])

        return err

    def compare_images(self, imageApath, imageBpath):
        """
        compute the mean squared error and structural similarity index for the images

        :param imageApath: Path to imageA
        :type imageApath: str
        :param imageBpath: Path to imageB
        :type imageBpath: str
        :return: True if equal, False if not equal
        :rtype: bool
        """

        try:
            imageA = cv2.imread(imageApath)
            imageB = cv2.imread(imageBpath)

            imageA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
            imageB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
        except FileNotFoundError:
            raise

        m = self.mse(imageA, imageB)
        s = ssim(imageA, imageB)

        self.logger.debug(
            f"Compared {imageApath} to {imageBpath} --> MSE: {m} and SSIM: {s}"
        )

        if m < 1.0 and round(s, 2) == 1.0:
            return True
        else:
            return False

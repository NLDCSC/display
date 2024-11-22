import logging

import cv2
import numpy as np
from nldcsc.loggers.app_logger import AppLogger
from skimage.metrics import structural_similarity as ssim

logging.setLoggerClass(AppLogger)


class CompareScreenshots(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def mse(image_a: np.ndarray, image_b: np.ndarray) -> float:
        """
        The 'Mean Squared Error' between the two images is the sum of the squared difference between the two images;

        NOTE: the two images must have the same dimension

        :param image_a: cv2.imread representation of image
        :param image_b: cv2.imread representation of image
        :return: return the MSE, the lower the error, the more "similar" the two images are
        """

        err = np.sum((image_a.astype("float") - image_b.astype("float")) ** 2)
        err /= float(image_a.shape[0] * image_a.shape[1])

        return err

    def compare_images(self, image_apath: str, image_bpath: str) -> bool:
        """
        compute the mean squared error and structural similarity index for the images

        :param image_apath: Path to imageA
        :param image_bpath: Path to imageB
        :return: True if equal, False if not equal
        """

        try:
            imageA = cv2.imread(image_apath)
            imageB = cv2.imread(image_bpath)

            imageA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
            imageB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
        except FileNotFoundError:
            raise

        m = self.mse(imageA, imageB)
        s = ssim(imageA, imageB)

        self.logger.debug(
            f"Compared {image_apath} to {image_bpath} --> MSE: {m} and SSIM: {s}"
        )

        if m < 1.0 and round(s, 2) == 1.0:
            return True
        else:
            return False

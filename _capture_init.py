import cv2
import time
import datetime
import os
import numpy as np
import image_processing as improc
import math_operation as mo
import _vehicle_init as vehicleInit

from PyQt4 import QtGui, QtCore
from PyQt4 import uic
from cv2 import ocl
from munkres import Munkres

ocl.setUseOpenCL(False)  # set flag OCL to False if you build OPENCV -D WITH_OPENCL=ON

class QtCapture:
    def setVideoMode(self, video_mode):
        self.video_mode = video_mode

    def getVideoMode(self):
        return self.video_mode

    def setBackgroundSubtraction(self, backgroundSubtraction):
        self.backgroundSubtracion = backgroundSubtraction

    def getBackgroundSubtraction(self):
        return self.backgroundSubtracion

    def setBoundary(self, boundary):
        self.boundary = boundary

    def getBoundary(self):
        return self.boundary

    def setROI(self, roi):
        self.roi = roi

    def getROI(self):
        return self.roi

    def setFPS(self, fps):
        self.fps = fps

    def getFPS(self):
        return self.fps

    def setAlt(self, alt):
        self.alt = alt

    def getAlt(self):
        return self.alt

    def setElevated(self, elevated):
        self.elevated = elevated

    def getElevated(self):
        return self.elevated

    def setFocal(self, focal):
        self.focal = focal

    def getFocal(self):
        return self.focal

    def setFOV(self, fov):
        self.fov = fov

    def getFOV(self):
        return self.fov

    def setLengthLV(self, lenghtLV):
        self.lengthLV = lenghtLV

    def getLengthLV(self):
        return self.lengthLV

    def setWidthLV(self, widthLV):
        self.widthLV = widthLV

    def getWidthLV(self):
        return self.widthLV

    def setHighLV(self, highLV):
        self.highLV = highLV

    def getHighLV(self):
        return self.highLV

    def setLengthHV(self, lenghtHV):
        self.lengthHV = lenghtHV

    def getLengthHV(self):
        return self.lengthHV

    def setWidthHV(self, widthHV):
        self.widthHV = widthHV

    def getWidthHV(self):
        return self.widthHV

    def setHighHV(self, highHV):
        self.highHV = highHV

    def getHighHV(self):
        return self.highHV

    def setDetectionLine(self, x1, y1, x2, y2):
        self.detectX1 = int(x1)
        self.detectY1 = int(y1)
        self.detectX2 = int(x2)
        self.detectY2 = int(y2)

    def getDetectionLine(self):
        return self.detectX1, self.detectY1, self.detectX2, self.detectY2

    def setRegistrationLine(self, x1, y1, x2, y2):
        self.registX1 = int(x1)
        self.registY1 = int(y1)
        self.registX2 = int(x2)
        self.registY2 = int(y2)

    def getRegistrationLine(self):
        return self.registX1, self.registY1, self.registX2, self.registY2

    def __init__(self, filename, frame):
        self.video_frame = frame

        # Global variable
        self.start_time = None
        self.width_frame = 1120  # pixel
        self.height_frame = 630  # pixel
        self.init_time = 5  # second /fps (fps 30) -> 24/30 = 0.8 -> 8 second
        self.mask_status = False
        self.mask_frame = None
        self.frame = 0
        self.total_LV = 0
        self.total_HV = 0
        self.totalVehicle = 0
        self.initMOG2 = cv2.createBackgroundSubtractorMOG2()  # Mixture of Gaussian initialization
        self.initMOG = cv2.bgsegm.createBackgroundSubtractorMOG()
        self.avg = 0
        self.tempList = []
        self.currentListVehicle = []
        self.tempID = 0

        # Start Capture Video
        self.cap = cv2.VideoCapture(filename)

        # Initiation vehicle module
        self.vehicle = vehicleInit.vehicle

        # Initiation file
        now = datetime.datetime.now()
        formatDate = now.strftime("%d-%m-%Y %H-%M")
        #self.file = open("output/{0}.csv".format(formatDate), "a")
        #if os.stat("output/{0}.csv".format(formatDate)).st_size == 0:
        #    self.file.write("No,Waktu,Jenis Kendaraan,Panjang,Lebar,Gambar\n")

        # Initiation folder
        path = "output"
        #self.formatFolder = now.strftime("{0}/%d-%m-%Y %H-%M").format(path)
        #if not os.path.isdir(self.formatFolder):
        #    os.makedirs(self.formatFolder)

        # Initiation to moving average
        _, PrimImg_frame = self.cap.read()
        PrimImg_frame = improc.cvtBGR2RGB(PrimImg_frame)
        PrimImg_frame = cv2.resize(PrimImg_frame, (self.width_frame, self.height_frame))
        self.avg = np.float32(PrimImg_frame)

    def start(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.nextFrame)
        self.timer.start(1000. / self.getFPS())
        self.start_time = time.time()

    def getrealFPS(self):
        self.realfps = QtCore.QTimer()
        self.realfps.start(1000.)

    def stop(self):
        self.timer.stop()

    def deleteLater(self):
        self.frame = 0
        self.total_HV = 0
        self.total_LV = 0
        # Stop capture
        self.cap.release()

        # Closing file
        #self.file.write("FOV:" + "," + str(self.getFOV()) + "\n" +
        #                "Focal:" + "," + str(self.getFocal()) + "\n" +
        #                "Angle:" + "," + str(self.getElevated()) + "\n" +
        #                "Altitude:" + "," + str(self.getAlt()) + "\n" +
        #                "Total LV:" + "," + str(self.total_LV) + "\n" +
        #                "Total HV:" + "," + str(self.total_HV) + "\n" +
        #                "Total Vehicle:" + "," + str(self.total_HV + self.total_LV) + "\n")
        #self.file.flush()
        #self.file.close()

    def nextFrame(self):
        real_time = time.time()
        ret, PrimImg_frame = self.cap.read()
        self.frame += 1

        # ----------- Do not disturb this source code ---------- #
        # Default color model is BGR format
        PrimResize_frame = cv2.resize(PrimImg_frame, (self.width_frame, self.height_frame))
        PrimRGB_frame = improc.cvtBGR2RGB(PrimResize_frame)

        # ------ [1] Initiation background subtraction ----------#
        # Initial State (IS)   : RGB - primary frame
        # Final State (FS)     : Binary - foreground frame
        if self.getBackgroundSubtraction() == "MA":  # if choose Moving Average

            # Moving Average subtraction
            cvtScaleAbs = improc.backgroundSubtractionAverage(PrimRGB_frame, self.avg, 0.01)
            movingAverage_frame = cvtScaleAbs
            initBackground = improc.initBackgrounSubtraction(real_time, self.start_time, self.init_time)

        else:  # If choose Mixture of Gaussian
            # Mixture of Gaussian Model Background Subtraction
            MOG_frame = self.initMOG.apply(PrimRGB_frame)

        if initBackground is False:
            font = cv2.FONT_HERSHEY_SIMPLEX
            size = 0.5
            color = (255, 255, 0)
            thick = 2
            cv2.putText(PrimRGB_frame, "Initialisations Background", (self.width_frame / 2, self.height_frame / 2), font, size, color, thick)

        # --- [x] Convert to Different Color Space ----------------#
        # IS    :
        # FS    :
        if self.getBackgroundSubtraction() == "MA":
            PrimGray_frame = improc.cvtRGB2GRAY(PrimRGB_frame)
            BackgroundGray_frame = improc.cvtRGB2GRAY(movingAverage_frame)

            PrimHSV_frame = cv2.cvtColor(PrimRGB_frame, cv2.COLOR_RGB2HSV)
            BackgroundHSV_frame = cv2.cvtColor(movingAverage_frame, cv2.COLOR_RGB2HSV)

            PrimLAB_frame = cv2.cvtColor(PrimRGB_frame, cv2.COLOR_RGB2LAB)
            BackgroundLAB_frame = cv2.cvtColor(movingAverage_frame, cv2.COLOR_RGB2LAB)

            PrimHue, PrimSat, PrimVal = cv2.split(PrimHSV_frame)
            BackHue, BackSat, BackVal = cv2.split(BackgroundHSV_frame)

            PrimLight, PrimA, PrimB = cv2.split(PrimLAB_frame)
            BackLight, BackA, BackB = cv2.split(BackgroundLAB_frame)

        # -- [x] Background Extraction ---------------------------#
        # IS    :
        # FS    :

            ImgDiffRGB = cv2.absdiff(PrimGray_frame, BackgroundGray_frame)
            ImgDiffHSV = cv2.absdiff(PrimVal, BackVal)
            ImgDiffLAB = cv2.absdiff(PrimLight, BackLight)

            combineRGBHSV = cv2.bitwise_or(ImgDiffRGB, ImgDiffHSV)
            combineLABHSV = cv2.bitwise_or(ImgDiffLAB, ImgDiffHSV)

            # -- [x] Smoothing and Noise Reduction --------------------#
            # IS    :
            # FS    :
            blurLevel = 21
            # averageBlur = cv2.blur(combineRGBHSV, (blurLevel, blurLevel))
            # medianBlur = cv2.medianBlur(combineRGBHSV, blurLevel)
            gaussianBlur_frame = cv2.GaussianBlur(combineRGBHSV, (blurLevel, blurLevel), 0)

            # -- [x] Thresholds to Binary ----------------------------#
            # IS    :
            # FS    :
            thresholdLevel = 30
            _, threshold = cv2.threshold(gaussianBlur_frame, thresholdLevel, 255, cv2.THRESH_BINARY)
            # _, blur1threshold = cv2.threshold(averageBlur, thresholdLevel, 255, cv2.THRESH_BINARY)
            # _, blur2threshold = cv2.threshold(gaussianBlur_frame, thresholdLevel, 255, cv2.THRESH_BINARY)

        else:  # Mixture of Gaussian
            _, threshold = cv2.threshold(MOG_frame, 100, 255, cv2.THRESH_OTSU)

        bin_frame = threshold.copy()
        # -- [x] Draw Detection and RegistrationLine -------------#
        # IS    :
        # FS    :
        thick = 2
        detectLine_color = (255, 0, 0)
        registLine_color = (0, 0, 255)

        detectX1, detectY1, detectX2, detectY2 = self.getDetectionLine()
        registX1, registY1, registX2, registY2 = self.getRegistrationLine()

        if self.getROI():
            cv2.line(PrimRGB_frame, (detectX1, detectY1), (detectX2, detectY2), detectLine_color, thick)
            cv2.line(PrimRGB_frame, (registX1, registY1), (registX2, registY2), registLine_color, thick)

        # -- [x] Draw information text ---------------------------#
        # IS    :
        # FS    :
        size = 0.6
        font = cv2.FONT_HERSHEY_DUPLEX
        LV_color = (255, 0, 0)
        Hv_color = (0, 0, 255)
        Frame_color = (255, 255, 255)

        cv2.putText(PrimRGB_frame, "Frame : {0}".format(self.frame), (1000, 20), font, 0.5, Frame_color, 1)
        cv2.putText(PrimRGB_frame, "Light Vehicle  : {0}".format(self.total_LV), (10, 600), font, size, LV_color, 1)
        cv2.putText(PrimRGB_frame, "Heavy Vehicle : {0}".format(self.total_HV), (10, 620), font, size, Hv_color, 1)

        # -- [x] Morphological Operation -------------------------#
        # IS    : ~
        # FS    : ~
        kernel = np.array([
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0]], dtype=np.uint8)

        morph_frame = cv2.erode(bin_frame, kernel, iterations=1)
        morph_frame = cv2.dilate(morph_frame, kernel, iterations=2)
        morph_frame = cv2.erode(morph_frame, kernel, iterations=2)

        kernel = np.array([
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1]], dtype=np.uint8)

        morph_frame = cv2.erode(morph_frame, kernel, iterations=2)
        morph_frame = cv2.dilate(morph_frame, kernel, iterations=2)
        morph_frame = cv2.erode(morph_frame, kernel, iterations=1)
        morph_frame = cv2.dilate(morph_frame, kernel, iterations=2)

        # -- [x] Mask Boundary ROI ------------------------------#
        # IS    : ~
        # FS    : ~
        color = (255, 255, 0)
        roiThreshold = 10

        ImgZero_frame = np.zeros((self.height_frame, self.width_frame), np.uint8)
        x1ROI = mo.funcX_line(detectX1, detectY1, registX1, registY1, 0)
        x2ROI = mo.funcX_line(detectX2, detectY2, registX2, registY2, 0)
        x3ROI = mo.funcX_line(detectX1, detectY1, registX1, registY1, self.height_frame)
        x4ROI = mo.funcX_line(detectX2, detectY2, registX2, registY2, self.height_frame)

        pts = np.array([
            [x1ROI - roiThreshold, 0], [x2ROI + roiThreshold, 0],
            [x4ROI + roiThreshold, self.height_frame], [x3ROI - roiThreshold, self.height_frame]])

        cv2.fillPoly(ImgZero_frame, [pts], color)

        roiBinary_frame = cv2.bitwise_and(ImgZero_frame, bin_frame)

        # -- [x] Mask RGB Frame and Binary Frame ----------------#
        # IS    : ~
        # FS    : ~
        ThreeChanelBinary_frame = improc.cvtGRAY2RGB(threshold)
        maskRGBandBin_frame = cv2.bitwise_and(PrimRGB_frame, ThreeChanelBinary_frame)
        Canny_EdgeDetection = cv2.Canny(maskRGBandBin_frame, 100, 150)

        # -- [x] Contour Detection ------------------------------#
        # IS    :
        # FS    :

        image, contours, hierarchy = cv2.findContours(roiBinary_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        contoursList = len(contours)

        for i in range(0, contoursList):
            cnt = contours[i]
            areaContours = cv2.contourArea(cnt)
            xContour, yContour, widthContour, highContour = cv2.boundingRect(cnt)
            # Point A : (xContour, yContour)
            # Point B : (xContour + widthContour, yContour)
            # Point C : (xContour + widthContour, yContour + highContour)
            # Point D : (xContour, yContour + highContour)
            areaBoundary = widthContour * highContour

            # -- [x] Pin Hole Model -------------------------#
            # IS    :
            # FS    :
            fov = self.getFOV()
            focal = self.getFocal() * 3.779527559055
            theta = self.getElevated()
            altitude = self.getAlt()
            maxHighLV = self.getHighLV()
            maxHighHV = self.getHighHV()
            maxLengthLV = self.getLengthLV()
            maxLengthHV = self.getLengthHV()
            maxWidthHV = self.getWidthHV()

            x1Vehicle = (yContour + highContour)
            x2Vehicle = yContour

            if self.getFocal() == 0.0:
                horizontalFOV, verticalFOV = mo.transformDiagonalFOV(fov)
                focal = mo.getFocalfromFOV(self.height_frame, verticalFOV)

            lengthVehicle = mo.vertikalPinHoleModel(self.height_frame, focal, altitude, theta, x1Vehicle, x2Vehicle, maxHighLV, maxHighHV, maxLengthLV)
            centerVehicle = mo.centeroidPinHoleMode(self.height_frame, focal, altitude, theta, (yContour + highContour))

            if self.getFocal() == 0.0:
                focal = mo.getFocalfromFOV(self.width_frame, horizontalFOV)

            widthVehicle = mo.horizontalPinHoleModel(self.width_frame, focal, altitude, xContour, (xContour + widthContour), centerVehicle)

            # -- [x] Draw Boundary -----------------------#
            # IS    :
            # FS    :
            colorLV = (0, 255, 0)
            colorHV = (0, 0, 255)
            thick = 2
            size = 2
            areaThreshold = 40

            if (widthVehicle >= 1.5) and (widthVehicle <= 8.0) and (lengthVehicle >= 1.5) and (lengthVehicle < maxLengthHV) and (areaContours >= (float(areaBoundary) * (float(areaThreshold) / 100))):
                # Get moment for centroid
                Moment = cv2.moments(cnt)
                xCentroid = int(Moment['m10'] / Moment['m00'])
                yCentroid = int(Moment['m01'] / Moment['m00'])

                # -- [x] Vehicle Classification -------------#
                # IS    :
                # FS    :
                if lengthVehicle <= maxLengthLV:
                    vehicleClassification = "LV"
                    color = colorLV
                else:
                    vehicleClassification = "HV"
                    color = colorHV

                if self.getBoundary():
                    cv2.rectangle(PrimRGB_frame, (xContour + widthContour, yContour + highContour), (xContour, yContour), color, thick)
                    # cv2.circle(PrimRGB_frame, (xCentroid, yCentroid), size, (0, 0, 255), thick)
                    improc.addText(bin_frame, lengthVehicle, size, xContour, (yContour - 3))

                # -- [x] Set Vehicle Identity ---------------#
                # IS    :
                # FS    :
                if self.currentListVehicle.__len__() == 0:
                    self.tempList.append(self.vehicle(self.totalVehicle + 1, xCentroid, yCentroid, lengthVehicle, widthVehicle, vehicleClassification, xContour, yContour, widthContour, highContour, 0))
                    self.currentListVehicle = self.tempList
                else:
                    self.tempList.append(self.vehicle(self.totalVehicle + 1, xCentroid, yCentroid, lengthVehicle, widthVehicle, vehicleClassification, xContour, yContour, widthContour, highContour, 0))

        tracking = True
        # -- [x] Vehicle Tracking -------------------------------#
        # IS    :
        # FS    : Hungarian algorithm by munkres
        if self.currentListVehicle.__len__() != 0 and self.tempList.__len__() != 0 and tracking is True:
            distance = [[0 for i in range(self.currentListVehicle.__len__())] for j in range(self.tempList.__len__())]
            for i in range(self.currentListVehicle.__len__()):
                for j in range(self.tempList.__len__()):
                    x1 = self.currentListVehicle[i].xCoordinate
                    y1 = self.currentListVehicle[i].yCoordinate
                    x2 = self.tempList[j].xCoordinate
                    y2 = self.tempList[j].yCoordinate
                    distance[j][i] = mo.distancetwoPoint(x1, y1, x2, y2)

            hungarian = Munkres()
            indexes = hungarian.compute(distance)
            total = 0

            for row, column in indexes:
                value = distance[row][column]
                total += value
                self.tempList[row].vehicleID = self.currentListVehicle[column].vehicleID
                self.tempList[row].lifetime = self.currentListVehicle[column].lifetime
            # -- [x] Counting Detection -----------------------------#
            # IS    :
            # FS    :

            for i in range(self.currentListVehicle.__len__()):
                stopGap = 80
                changeRegistLine_color = (255, 255, 255)
                changeThick = 4

                vehicleID = self.tempList[i].vehicleID
                xCentroid = self.tempList[i].xCoordinate
                yCentroid = self.tempList[i].yCoordinate
                lengthVehicle = self.tempList[i].vehicleLength
                vehicleClassification = self.tempList[i].vehicleClass
                vehicleLifeTime = self.tempList[i].lifetime

                print xCentroid, yCentroid, self.currentListVehicle.__len__()

                cv2.circle(PrimRGB_frame, (xCentroid, yCentroid), size, (0, 0, 255), thick)
                cv2.putText(PrimRGB_frame, "{0}".format(vehicleID), (xCentroid + 1, yCentroid + 1), font, 1, (0, 0, 255))

                yPredictDetect = mo.funcY_line(detectX1, detectY1, detectX2, detectY2, xCentroid)
                yPredictRegist = mo.funcY_line(registX1, registY1, registX2, registY2, xCentroid)
                countClass = improc.initCounting(registX1, registY1, registX2, registX2, xCentroid, yPredictRegist, vehicleClassification)

                if (yCentroid < yPredictRegist + stopGap) and (xCentroid >= detectX1) and (xCentroid <= detectX2) and (vehicleLifeTime == 0):
                    self.currentListVehicle[i].lifetime = 1

                if (yCentroid >= yPredictRegist) and (yCentroid < yPredictRegist + stopGap) and (xCentroid >= registX1) and (xCentroid <= registX2) and (vehicleLifeTime == 1):
                    if countClass == "LV":
                        self.total_LV += 1
                    elif countClass == "HV":
                        self.total_HV += 1

                    self.totalVehicle = self.total_LV + self.total_HV
                    self.currentListVehicle[i].lifetime = 0

                    improc.addText(PrimRGB_frame, vehicleID, size, (xCentroid + 5), (yCentroid - 5))
                    cv2.line(bin_frame, (registX1, registY1), (registX2, registY2), changeRegistLine_color, changeThick)
                    print "Total LV: {0} | Total HV: {1} | class: {2} length: {3} width: {4}".format(self.total_LV, self.total_HV, countClass, lengthVehicle, widthVehicle)

                    # -- [x] Crop Image -------------------------#
                    # IS    :
                    # FS    :
                    xContour = self.tempList[i].xContour
                    yContour = self.tempList[i].yContour
                    widthContour = self.tempList[i].widthContour
                    highContour = self.tempList[i].highContour

                    now = datetime.datetime.now()
                    formatDate = now.strftime("%d%m%Y_%H%M%S")

                    # formatFileName = "{0}/{1}_{2:03}_{3}.jpg".format(self.formatFolder, countClass, (self.total_LV + self.total_HV), formatDate)
                    # cropping_frame = PrimResize_frame[yContour:yContour + highContour, xContour:xContour + widthContour]
                    # cv2.imwrite(formatFileName, cropping_frame)

                    # -- [x] Save Filename to Text --------------#
                    # IS    :
                    # FS    :
                    formatDate = now.strftime("%d:%m:%Y %H:%M:%S")
                    #self.file.write(str(self.totalVehicle) + "," +
                    #                str(formatDate) + "," +
                    #                str(countClass) + "," +
                    #                str(lengthVehicle) + "," +
                    #                str(widthVehicle) + "," +
                    #                str(formatFileName) + "\n")
                    #self.file.flush()

        # Return variable
        self.tempList = []

        # ---------- Do not disturb this source code ----------- #
        if self.getVideoMode() == "RGB":
            show_frame = PrimRGB_frame
            img = QtGui.QImage(show_frame, show_frame.shape[1], show_frame.shape[0], QtGui.QImage.Format_RGB888)
            # RGB image - Format_RGB888
        else:
            show_frame = bin_frame
            img = QtGui.QImage(show_frame, show_frame.shape[1], show_frame.shape[0], QtGui.QImage.Format_Indexed8)
            # Gray scale, binary image - Format_Indexed8

        pix = QtGui.QPixmap.fromImage(img)
        self.video_frame.setPixmap(pix)

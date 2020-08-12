#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
import os
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from lxml import etree
import codecs
from libs.constants import DEFAULT_ENCODING
from libs.utils import read_json, write_json

JSON_EXT = '.json'

class DMPRWriter:

    def __init__(self, foldername, filename, imgSize, databaseSrc='Unknown', localImgPath=None):
        self.foldername = foldername
        self.filename = filename
        self.databaseSrc = databaseSrc
        self.imgSize = imgSize
        self.boxlist = []
        self.localImgPath = localImgPath
        self.verified = False

    def addBndBox(self, xmin, ymin, xmax, ymax, name, difficult):
        bndbox = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}
        bndbox['name'] = name
        bndbox['difficult'] = difficult
        self.boxlist.append(bndbox)

    def BndBox2YoloLine(self, box, classList=[]):
        xmin = box['xmin']
        xmax = box['xmax']
        ymin = box['ymin']
        ymax = box['ymax']

        # PR387
        boxName = box['name']
        if boxName not in classList:
            classList.append(boxName)

        classIndex = classList.index(boxName)

        return classIndex, xmin, ymin, xmax, ymax

    def save(self, classList=[], targetFile=None):

        out_file = None #Update yolo .txt
        out_class_file = None   #Update class list .txt

        markers = {
            'marks': []
        }
        for box in self.boxlist:
            classIndex, xmin, ymin, xmax, ymax = self.BndBox2YoloLine(box, classList)
            markers['marks'].append(xmin, ymin, xmax, ymax, classIndex)

        labels = {
            'classList': classList
        }
        
        write_json(self.filename + JSON_EXT, markers)
        write_json(os.path.join(os.path.dirname(os.path.abspath(self.filename)), "classes.json"), labels)

class DMPRReader:

    def __init__(self, filepath, image, classListPath=None):
        # shapes type:
        # [labbel, [(x1,y1), (x2,y2), (x3,y3), (x4,y4)], color, color, difficult]
        self.shapes = []
        self.filepath = filepath

        if classListPath is None:
            dir_path = os.path.dirname(os.path.realpath(self.filepath))
            self.classListPath = os.path.join(dir_path, "classes.json")
        else:
            self.classListPath = classListPath

        # print (filepath, self.classListPath)

        # classesFile = open(self.classListPath, 'r')
        self.classes = read_json(self.classListPath)['classList']

        # print (self.classes)

        imgSize = [image.height(), image.width(),
                      1 if image.isGrayscale() else 3]

        self.imgSize = imgSize

        self.verified = False
        # try:
        self.parseDMPRFormat()
        # except:
            # pass

    def getShapes(self):
        return self.shapes

    def addShape(self, label, xmin, ymin, xmax, ymax, difficult):
        points = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
        self.shapes.append((label, points, None, None, difficult))

    def yoloLine2Shape(self, classIndex, xmin, ymin, xmax, ymax):
        label = self.classes[int(classIndex)]

        return label, xmin, ymin, xmax, ymax

    def parseDMPRFormat(self):
        # bndBoxFile = open(self.filepath, 'r')
        bndBoxFile = read_json(self.filepath)
        for bndBox in bndBoxFile['marks']:
            # if len(bndBox) == 6: # ODMPR
            #     xmin, ymin, xmax, ymax, classIndex, angle = bndBox
            # else: # Classic DMPR
            xmin, ymin, xmax, ymax, classIndex = bndBox

            label, xmin, ymin, xmax, ymax = self.yoloLine2Shape(classIndex, xmin, ymin, xmax, ymax)

            # Caveat: difficult flag is discarded when saved as yolo format.
            self.addShape(label, xmin, ymin, xmax, ymax, False)

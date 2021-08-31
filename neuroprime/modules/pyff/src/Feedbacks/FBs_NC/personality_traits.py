#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 22 16:59:02 2018

@author: nm.costa
"""
import codecs

from HTMLParser import HTMLParser



# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
    DATA = []
    def handle_starttag(self, tag, attrs):
        print "Encountered a start tag:", tag

    def handle_endtag(self, tag):
        print "Encountered an end tag :", tag

    def handle_data(self, data):
        print "Encountered some data  :", data
        self.DATA.append(data)

def remove_item(LIST, item):
    #Strip of ""
    #LIST = map(lambda s: s.strip(), LIST)
    # List comprehension
    LIST = [x for x in LIST if x != item]
    return LIST

def remove_newlines(LIST):
    #Strip of "\n"
    LIST = map(lambda s: s.strip(), LIST)
    # List comprehension remove item
    LIST = remove_item(LIST, '')
    return LIST

def allindices(string, sub, listindex=[], offset=0):
    i = string.find(sub, offset)
    while i >= 0:
        listindex.append(i)
        i = string.find(sub, i + 1)
    return listindex

# instantiate the parser and fed it some HTML
parser = MyHTMLParser()
f=codecs.open("traits.htm", 'r')
parser.feed(f.read())

FinalDataList = remove_newlines(parser.DATA)
print (FinalDataList)
positive_traits = FinalDataList[1:237]
neutral_traits = FinalDataList[237:350]
negative_traits = FinalDataList[350:]
#Break by type of traits


# Save Data test
FILENAME = "Traits.txt"
with open (FILENAME,'w') as fileOutput:
    for item in FinalDataList:
        fileOutput.write("%s\n" % item)
FILENAME = "PositiveTraits.txt"
with open (FILENAME,'w') as fileOutput:
    for item in positive_traits:
        fileOutput.write("%s\n" % item)
FILENAME = "NeutralTraits.txt"
with open (FILENAME,'w') as fileOutput:
    for item in neutral_traits:
        fileOutput.write("%s\n" % item)
FILENAME = "NegativeTraits.txt"
with open (FILENAME,'w') as fileOutput:
    for item in negative_traits:
        fileOutput.write("%s\n" % item)

#load data test
with open("PositiveTraits.txt", 'r') as fin:
    positive_traits = [line.rstrip('\n') for line in fin]
    print (positive_traits)
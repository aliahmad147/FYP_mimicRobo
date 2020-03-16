# !/usr/bin/python
# -*- coding: utf-8 -*-

"""
@created: 2019-9-23 13:40:00
@author: Ali Ahmad Mansoor
"""
from __future__ import print_function
import sys
import pandas as pd
import numpy as np
from mythread import mythread
import pyttsx3
import threading
from time import sleep
import time
from threading import Timer

# from tkinter import font
# from docx.enum.text import WD_COLOR
# from docx.enum.text import WD_COLOR_INDEX
engine = pyttsx3.init()
rate = engine.getProperty('rate')
engine.setProperty('rate', 150)

print("Python:", sys.version)

try:
    import wx

    print("wxPython:", wx.version())
except:
    raise SystemExit(__file__ + " needs wxPython.")

try:
    import fitz

    print(fitz.__doc__)
except:
    raise SystemExit(__file__ + " needs PyMuPDF(fitz).")

try:
    from PageFormat import FindFit
except ImportError:
    def FindFit(*args):
        return "not implemented"

try:
    from icons import ico_pdf  # PDF icon in upper left screen corner

    do_icon = True
except ImportError:
    do_icon = False
app = None
app = wx.App()
assert wx.VERSION[0:3] >= (3, 0, 2), "need wxPython 3.0.2 or later"
assert tuple(map(int, fitz.VersionBind.split("."))) >= (1, 9, 2), "need PyMuPDF 1.9.2 or later"

# make some adjustments for differences between wxPython versions 3.0.2 / 3.0.3
if wx.VERSION[0:3] >= (3, 0, 3):
    cursor_hand = wx.Cursor(wx.CURSOR_HAND)
    cursor_norm = wx.Cursor(wx.CURSOR_DEFAULT)
    bmp_buffer = wx.Bitmap.FromBuffer
    phoenix = True
else:
    cursor_hand = wx.StockCursor(wx.CURSOR_HAND)
    cursor_norm = wx.StockCursor(wx.CURSOR_DEFAULT)
    bmp_buffer = wx.BitmapFromBuffer
    phoenix = False

if str != bytes:
    stringtypes = (str, bytes)
else:
    stringtypes = (str, unicode)


def getint(v):
    try:
        return int(v)
    except:
        pass
    if type(v) not in stringtypes:
        return 0
    a = "0"
    for d in v:
        if d in "0123456789":
            a += d
    return int(a)


# abbreviations to get rid of those long pesky names ...
# ==============================================================================
# Define our dialog as a subclass of wx.Dialog.
# Only special thing is, that we are being invoked with a filename ...
# ==============================================================================
class PDFdisplay(wx.Dialog):
    def __init__(self, parent, filename):
        self.file_name = filename
        defPos = wx.DefaultPosition

        defSiz = wx.DefaultSize
        print(defPos, defSiz)
        self.flag_OnOff = True
        zoom = 1  # zoom factor of display
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY,
                           title=u"Display with PyMuPDF: ",
                           pos=defPos, size=defSiz,
                           style=wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX |
                                 wx.RESIZE_BORDER)

        # ======================================================================
        # display an icon top left of dialog, append filename to title
        # ======================================================================
        if do_icon:
            self.SetIcon(ico_pdf.img.GetIcon())  # set a screen icon
        self.SetTitle(self.Title + filename)
        self.SetBackgroundColour(wx.Colour(240, 230, 140))
        self.currentZoom = 0
        self.slider = wx.Slider(self, value=10, minValue=1, maxValue=100, style=wx.SL_HORIZONTAL | wx.SL_LABELS)

        # ======================================================================
        # open the document with MuPDF when dialog gets created
        # ======================================================================
        self.doc = fitz.open(filename)  # create Document object
        self.no_pages = len(self.doc)
        self.current_page = 1
        # self.doc1 = fitz.open(filename)
        self.doc.select([0])
        self.file_data = ''
        self.doc.save("page_.pdf", garbage=3)
        self.doc.close()

        self.doc1 = fitz.open("page_.pdf")
        self.doc = fitz.open(filename)  # create Document object

        # new_pdf=fitz.ope

        # self.selected_page =self.doc.select([0])

        if self.doc.needsPass:  # check password protection
            self.decrypt_doc()
        if self.doc.isEncrypted:  # quit if we cannot decrpt
            self.Destroy()
            return
        self.dl_array = [0] * self.no_pages
        self.last_page = -1  # memorize last page displayed
        self.link_rects = []  # store link rectangles here
        self.link_texts = []  # store link texts here
        self.current_idx = -1  # store entry of found rectangle
        self.current_lnks = []  # store entry of found rectangle
        self.currentword = 0

        # ======================================================================
        # define zooming matrix for displaying PDF page images
        # we increase images by 20%, so take 1.2 as scale factors
        # ======================================================================

        # fitz.Matrix(fitz.Identity)
        self.matrix = fitz.Matrix(fitz.Identity)  # will use a constant zoom

        '''
        =======================================================================
        Overall Dialog Structure:
        -------------------------
        szr10 (main sizer for the whole dialog - vertical orientation)
        +-> szr20 (sizer for buttons etc. - horizontal orientation)
          +-> button forward
          +-> button backward
          +-> field for page number to jump to
          +-> field displaying total pages
        +-> PDF image area
        =======================================================================
        '''

        # next word button
        self.ButtonNextW = wx.Button(self, wx.ID_ANY, u"next",
                                     defPos, defSiz, wx.BU_EXACTFIT)

        # forward button
        self.ButtonNext = wx.Button(self, wx.ID_ANY, u"forw",
                                    defPos, defSiz, wx.BU_EXACTFIT)

        # backward button
        self.ButtonPrevious = wx.Button(self, wx.ID_ANY, u"back",
                                        defPos, defSiz, wx.BU_EXACTFIT)
        self.Buttonspeak = wx.Button(self, wx.ID_ANY, u"speak",
                                     defPos, defSiz, wx.BU_EXACTFIT)

        self.ButtonStop = wx.Button(self, wx.ID_ANY, u"stop",
                                    defPos, defSiz, wx.BU_EXACTFIT)
        # ======================================================================
        # text field for entering a target page. wx.TE_PROCESS_ENTER is
        # required to get data entry fired as events.
        # ======================================================================
        self.TextToPage = wx.TextCtrl(self, wx.ID_ANY, u"1", defPos, wx.Size(40, -1),
                                      wx.TE_CENTRE | wx.TE_PROCESS_ENTER)
        # displays total pages and page paper format
        self.statPageMax = wx.StaticText(self, wx.ID_ANY,
                                         "of " + str(self.no_pages) + " pages.",
                                         defPos, defSiz, 0)
        self.links = wx.CheckBox(self, wx.ID_ANY, u"show links",
                                 defPos, defSiz, wx.ALIGN_LEFT)
        self.links.Value = True
        self.paperform = wx.StaticText(self, wx.ID_ANY, "", defPos, defSiz, 0)
        # define the area for page images and load page 1 for primary display
        self.PDFimage = wx.StaticBitmap(self, wx.ID_ANY, self.pdf_show(1, 0),
                                        defPos, defSiz, style=0)
        # ======================================================================
        # the main sizer of the dialog
        # ======================================================================
        self.szr10 = wx.BoxSizer(wx.VERTICAL)
        szr20 = wx.BoxSizer(wx.HORIZONTAL)
        szr20.Add(self.ButtonNext, 0, wx.ALL, 5)
        szr20.Add(self.ButtonPrevious, 0, wx.ALL, 5)

        szr20.Add(self.Buttonspeak, 0, wx.ALL, 5)
        szr20.Add(self.ButtonNextW, 0, wx.ALL, 5)
        szr20.Add(self.ButtonStop, 0, wx.ALL, 5)

        szr20.Add(self.TextToPage, 0, wx.ALL, 5)
        szr20.Add(self.statPageMax, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        szr20.Add(self.links, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        szr20.Add(self.paperform, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        # sizer ready, represents top dialog line
        self.szr10.Add(szr20, 0, wx.EXPAND, 5)

        # szr30 = wx.BoxSizer(wx.HORIZONTAL)
        # szr40 = wx.BoxSizer(wx.VERTICAL)

        self.szr10.Add(self.PDFimage, 0, wx.ALL | wx.EXPAND, 5)
        # szr30.Add(szr40,1, wx.EXPAND, 5)
        self.szr10.Add(self.slider, 0, flag=wx.SL_HORIZONTAL | wx.SL_RIGHT, border=20)

        # self.szr10.Add(szr30, 0, wx.EXPAND, 5)
        # main sizer now ready - request final size & layout adjustments
        self.szr10.Fit(self)
        self.SetSizer(self.szr10)
        self.Layout()
        # center dialog on screen
        self.Centre(wx.BOTH)

        # Bind buttons and fields to event handlers
        self.ButtonNext.Bind(wx.EVT_BUTTON, self.NextPage)
        self.ButtonPrevious.Bind(wx.EVT_BUTTON, self.PreviousPage)
        self.ButtonNextW.Bind(wx.EVT_BUTTON, self.highlight)
        self.Buttonspeak.Bind(wx.EVT_BUTTON, self.PreProcess)
        self.ButtonStop.Bind(wx.EVT_BUTTON, self.Stop_running)

        self.slider.Bind(wx.EVT_SLIDER, self.OnSliderScroll)
        self.TextToPage.Bind(wx.EVT_TEXT_ENTER, self.GotoPage)
        self.PDFimage.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
        self.PDFimage.Bind(wx.EVT_MOTION, self.move_mouse)
        self.PDFimage.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        # self.PreProcess()

    # ==============================================================================
    # Button handlers and other functions
    # ==============================================================================
    # t.start() # after 30 seconds, "hello, world" will be printed
    def OnSliderScroll(self, event):
        obj = event.GetEventObject()
        value = obj.GetValue()
        if 0 <= self.slider.GetValue() <= 33:
            self.currentZoom = self.slider.GetValue()
            print("1--", self.currentZoom)
            self.NeuesImage(self.current_page, 1)
            event.Skip()
        elif 33 < self.slider.GetValue() <= 66:
            self.currentZoom = self.slider.GetValue()
            print("3--", self.currentZoom)
            self.NeuesImage(self.current_page, 1)
            event.Skip()

        elif 66 < self.slider.GetValue() <= 100:
            print("3--", self.currentZoom)
            self.currentZoom = self.slider.GetValue()
            self.NeuesImage(self.current_page, 1)
            event.Skip()

    def fun1(self, line, b):
        try:
            # sleep(0.2)
            engine.say(line)
            engine.runAndWait()
        except:
            engine.endLoop()
            print("Error--")
            self.fun1(line, b)
        #finally:
        #    pyttsx3.engine.Engine.stop(engine)

            # pyttsx3.driver.DriverProxy.setBusy(engine, busy=False)

    def fun2(self):
        a = "The quick brown fox jumped in or over the lazy dog. he is good."
        s = "i am good."
        thread1 = threading.Thread(target=fun1, args=(s, 2))
        thread1.start()
        for i in range(9):
            sleep(0.17)
            print(i)
        thread1.join()
        print("End 1")

    def distance(self, point1, point2):
        if (point1 and point2):
            return point1[0] - point2[0], point1[1] - point2[1]

    def Not_Equal(self, point1, point2):
        if (point1 and point2):
            if (point1[0] == point2[0] and point1[1] == point2[1]):
                return 0
            else:
                return point1[1] - point2[1]

    def Stop_running(self, event):
        print("flag function")
        self.flag_OnOff = False

    def Speak(self, line):
        print("=> ", line)
        try:
            print("1-")
            engine.say(line)
            print("2-")
            engine.runAndWait()
            print("3-")
        except:
            engine.endLoop()
            print("Error--")
        finally:
            print("END")
            # pyttsx3.engine.Engine.stop(engine)

    def highlight1(self, event):
        self.NeuesImage(self.current_page, 0)
        event.Skip()
        data = pd.read_csv("test_page11.csv")
        page = 0
        self.currentword
        element = data.location[self.currentword]
        word = data.word[self.currentword]
        # for element in data.location:
        # print("--")
        element = element.replace(')', '')
        element = element.replace('(', '')
        element = element.replace(' ', '')
        Arr = element.split(',')
        arr2 = [float(i) for i in Arr]
        # Arr = np.array(Arr)
        # Arr = Arr.astype('float64')
        # arr2 = [Arr]
        highlight = self.doc1[page].addHighlightAnnot(arr2)
        self.NeuesImage(self.current_page, 1)
        event.Skip()
        # self.Speak( word)

        self.currentword += 1

    def wait_for(self, length):
        k = 0
        while k < length:
            k += 1
            #print(k),
        #time.sleep(1)
        return

    def highlight(self, event):
        print("press next button")
        self.file_data = pd.read_csv("test_page1.csv")
        page = 0
        for i in range(len(self.file_data.location)):
            # self.NeuesImage(self.current_page, 0)
            # event.Skip()
            # self.highlight1(self)
            # sleep(1.8)
            # self.NeuesImage(self.current_page, 1)
            # event.Skip()

            if self.currentword < len(self.file_data.location):
                element = self.file_data.location[self.currentword]
                try:

                    print(element)
                    element = element.replace(')', '')
                    element = element.replace('(', '')
                    element = element.replace(' ', '')
                    Arr = element.split(',')
                    arr2 = [float(i) for i in Arr]
                    print(arr2)

                    highlight = self.doc1[page].addHighlightAnnot(arr2)

                    try:
                        self.doc1.save("page_test.pdf", garbage=2)
                    except:
                        print("Except")
                        pass
                    #sleep(1.5)


                    self.NeuesImage(self.current_page, 1)
                    event.Skip()
                    self.wait_for(3000)

                    if self.flag_OnOff == False:
                        self.flag_OnOff = True
                        break
                    self.wait_for(1000)
                    # sleep(1.5)
                    self.currentword += 1
                    self.NeuesImage(self.current_page, 0)
                    event.Skip()
                    #self.wait_for(3000)
                except:
                    print("Exception...")


    def PreProcess(self, event):
        def compare_right(point1, point2):
            if point1 and point2:
                if point2[0] <= point1[0] and point2[1] <= point1[1]:
                    return True
                else:
                    return False

        def compare_left(point1, point2):
            if point1 and point2:
                if point2[0] >= point1[0] and point2[1] >= point1[1]:
                    return True
                else:
                    return False

        def Is_present(block, text_instances):
            # print(block,text_instances[0].bottom_left,text_instances[0].top_right)
            # print(text_instances)
            i = 0
            for inst in text_instances:
                # print(inst)
                if compare_left((block[0], block[1]), inst.top_left) and compare_left((block[0], block[3]),
                                                                                      inst.bottom_left):
                    print("left side theak ha")
                    if compare_right((block[2], block[3]), inst.bottom_right) and compare_right((block[2], block[1]),
                                                                                                inst.top_right):
                        print("right side bhe theak ha")
                        return True, i
                i += 1
            return False, 0

        def checkMin(prv_inst, insts):
            newDistance = 0
            counter = 0
            minDist1, minDist2 = distance(prv_inst.top_right, insts[0].top_left)
            for inst in insts:
                # print (prv_inst.top_left,prv_inst.top_right)
                # print (prv_inst.top_right,inst.top_left)

                a, b = distance(prv_inst.top_right, inst.top_left)

                # print ("A:B :",a,b)
                if ((minDist1 + minDist2) > (a + b)):
                    # print (prv_inst.top_right,inst.top_left)
                    # print (minDist1,minDist2)
                    minDist1 = a
                    minDist2 = b
                    newDistance = counter
                counter += 1
            return newDistance

        # page = pdf[0]
        # page.getTextBlocks(flags=None)
        page = 0

        def distance(point1, point2):
            if (point1 and point2):
                return abs(point1[0] - point2[0]), abs(point1[1] - point2[1])

        class Map1:
            def __init__(self, arr):
                self.array = arr
                self.counter = 0

            def get_array(self):
                return self.array

            def GetValue(self):
                if self.counter < (len(self.array) - 1):
                    self.counter += 1
                    return self.array[self.counter - 1]
                else:
                    print("Index Out Of Bound")
                    return 0

        def Not_Equal(point1, point2):
            if (point1 and point2):
                if (point1[0] == point2[0] and point1[1] == point2[1]):
                    return 0
                else:
                    return point1[1] - point2[1]

        iter = 0
        df1 = pd.DataFrame({"line": [], "location": []})
        df11 = pd.DataFrame({"word": [], "location": []})
        w_dist = {}
        for block in self.doc1[page].getTextBlocks(flags=None):
            Arr_1 = [float(block[0]), float(block[1]), float(block[2]), float(block[3])]
            text1 = block[4]
            lines = text1.split("\n")
            #    text = "constructive work. But since I feel that you are men of genuine good will"
            #    arr=text.split(' ')
            # print (lines)
            for line in lines:
                arr = line.split(' ')

                text_inst = self.doc1[page].searchFor(line)
                # print (text_inst)

                if (text_inst):
                    tup = Is_present(Arr_1, text_inst)
                    if tup[0]:
                        text_inst=text_inst[tup[1]]
                        print("-----", tup[1])
                        #print(text_inst[tup[1]])
                    else:
                        prv_inst = text_inst[0]
                        text_inst = text_inst[0]
                    iter += 1
                    '''
                    if (len(text_inst) > 1 and iter != 0):
                        # print ("cond")
                        flag2 = False
                        for i in text_inst:
                            # print ("previous ",prv_inst)
                            # print ("current",i)
                            if (i[1] != prv_inst[1] and i[2] != prv_inst[2]):
                                #   print ("----",prv_inst.bottom_left,i.bottom_left)
                                dis = abs(prv_inst.bottom_left[1] - i.bottom_left[1])

                                if (dis > 3):
                                    # print ("IDHR")
                                    text_inst = i
                                    prv_inst = i
                                    flag2 = True
                                    #      print ("cond_true")
                                    break
                        if (flag2 == False):
                            # print ("Yeh--",text_inst)
                            prv_inst = text_inst[0]
                            text_inst = text_inst[0]
                            '''


                    # print (text_inst)
                    # text_inst=text_inst[0]

                    # print (text_inst)
                    # print (text_inst.top_left)
                    count = 0
                    arr = arr[:len(arr)]
                    print(arr)
                    wor = 0
                    #       break
                    for w in arr:
                        if (w != ''):
                            #print(w)
                            flag3 = 0
                            flag = False
                            if (count == 0):
                                if w_dist.get(w + ' '):
                                    flag3 = 0
                                    text_instances = w_dist[w + ' '].get_array()
                                    pass
                                else:
                                    flag3 = 0
                                    text_instances = self.doc1[page].searchFor(w + ' ', hit_max=120)
                                    w_dist[w + ' '] = Map1(text_instances)
                            elif (count != (len(arr) - 1)):
                                if w_dist.get(' ' + w + ' '):
                                    flag3 = 1
                                    text_instances = w_dist[' ' + w + ' '].get_array()
                                    pass
                                else:
                                    flag3 = 1
                                    text_instances = self.doc1[page].searchFor(' ' + w + ' ', hit_max=120)
                                    w_dist[' ' + w + ' '] = Map1(text_instances)
                            elif (count == (len(arr) - 1)):
                                if w_dist.get(' ' + w):
                                    text_instances = w_dist[' ' + w].get_array()
                                    flag3 = 2
                                    pass
                                else:
                                    flag3 = 2
                                    text_instances = self.doc1[page].searchFor(' ' + w, hit_max=120)
                                    w_dist[' ' + w] = Map1(text_instances)

                            counter = 0
                            for inst in text_instances:

                                # if(inst.bottom_left[1]>text_inst.bottom_right[1]):
                                #    print ("idhr sa ruka")
                                #    break
                                # print ("LEFT",inst.top_left,inst.bottom_left)
                                # print ("RIght",text_inst.bottom_right,inst.bottom_left)
                                a, b = distance(text_inst.top_right, inst.top_left)
                                c, d = distance(text_inst.top_left, inst.top_left)
                                # print("If cond ",text_inst.top_right[0],inst.top_left[0])

                                if (c == 0 and d == 0):
                                    #  highlight = self.doc1[page].addHighlightAnnot(inst)
                                    df2 = pd.DataFrame(
                                        {"line": [str(iter)], "location": [(inst[0], inst[1], inst[2], inst[3])]})
                                    df3 = pd.DataFrame(
                                        {"word": [w], "location": [(inst[0], inst[1], inst[2], inst[3])]})
                                    df1 = df1.append(df2, ignore_index=True)
                                    df11 = df11.append(df3, ignore_index=True)
                                    # self.NeuesImage(self.current_page, 1)
                                    # event.Skip()
                                    # nparr = np.append(nparr, inst)
                                    #              print ("cond1",w,counter,inst)
                                    text_inst = inst
                                    if ((len(text_instances) - 1) >= (counter + 1)):
                                        if (int(text_inst.top_right[0]) == int(
                                                text_instances[counter + 1].top_left[0]) and wor <= 3):
                                            dis = abs(
                                                text_inst.bottom_right[1] - text_instances[counter + 1].bottom_left[1])
                                            if (dis <= 3):
                                                #                         print ("IDHR")
                                                #                        print ("cond1",w,counter,text_instances[counter+1])
                                                #            highlight = self.doc1[page].addHighlightAnnot(text_instances[counter + 1])
                                                df2 = pd.DataFrame({"line": [str(iter)], "location": [
                                                    (text_instances[counter + 1][0], text_instances[counter + 1][1],
                                                     text_instances[counter + 1][2], text_instances[counter + 1][3])]})
                                                df3 = pd.DataFrame({"word": [w], "location": [
                                                    (text_instances[counter + 1][0], text_instances[counter + 1][1],
                                                     text_instances[counter + 1][2], text_instances[counter + 1][3])]})
                                                df1 = df1.append(df2, ignore_index=True)
                                                df11 = df11.append(df3, ignore_index=True)
                                                #                                        nparr = np.append(nparr, text_instances[counter + 1])
                                                flag = True
                                                #           self.NeuesImage(self.current_page, 1)
                                                #          event.Skip()
                                                text_inst = text_instances[counter + 1]
                                                break
                                    flag = True
                                    break
                                elif (a <= 3 and b <= 3 and (
                                        int(text_inst.bottom_right[1]) == int(inst.bottom_left[1]))):

                                    # print (distance(text_inst.top_right,inst.top_left))
                                    # print (abs(distance1(text_inst.top_right,inst.top_left)))
                                    # highlight = self.doc1[page].addHighlightAnnot(inst)
                                    df2 = pd.DataFrame(
                                        {"line": [str(iter)], "location": [(inst[0], inst[1], inst[2], inst[3])]})
                                    df3 = pd.DataFrame(
                                        {"word": [w], "location": [(inst[0], inst[1], inst[2], inst[3])]})
                                    df1 = df1.append(df2, ignore_index=True)
                                    df11 = df11.append(df3, ignore_index=True)
                                    # self.NeuesImage(self.current_page, 1)
                                    # event.Skip()
                                    text_inst = inst
                                    flag = True
                                    break
                                counter += 1
                            if (flag == False):
                                print("Fun---", w, "--", text_inst, text_instances)
                                if (text_inst and text_instances):
                                    v = checkMin(text_inst, text_instances)
                                    # print (v,text_instances[v])
                                    highlight = self.doc1[page].addHighlightAnnot(text_instances[v])
                                    df2 = pd.DataFrame({"line": [str(iter)], "location": [
                                        (text_instances[v][0], text_instances[v][1],
                                         text_instances[v][2], text_instances[v][3])]})
                                    df3 = pd.DataFrame({"word": [w], "location": [
                                        (text_instances[v][0], text_instances[v][1],
                                         text_instances[v][2], text_instances[v][3])]})
                                    df1 = df1.append(df2, ignore_index=True)
                                    df11 = df11.append(df3, ignore_index=True)
                                    # self.NeuesImage(self.current_page, 1)
                                    # event.Skip()
                                    #                          nparr = np.append(nparr, text_instances[v])
                                    text_inst = text_instances[v]
                            #                        print ("Idhr bhe aata ha")
                            wor += 1
                    #    self.NeuesImage(self.current_page, 0)
                    #   event.Skip()
                else:
                    print("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh--------------------")

        df1.to_csv('test_page1.csv', index=False)
        df11.to_csv('test_page11.csv', index=False)
        print("Done")
        # sleep(2)
        # self.highlight(event)
        # self.NextPage(event)

    def OnLeftDown(self, evt):
        if self.current_idx < 0 or not self.links.Value:
            evt.Skip()
            return
        lnk = self.current_lnks[self.current_idx]
        if lnk["kind"] == fitz.LINK_GOTO:
            self.TextToPage.Value = str(lnk["page"] + 1)
            self.GotoPage(evt)
        elif lnk["kind"] == fitz.LINK_URI:
            import webbrowser
            try:
                webbrowser.open_new(self.link_texts[self.current_idx])
            except:
                pass
        elif lnk["kind"] == fitz.LINK_GOTOR:
            import subprocess
            try:
                subprocess.Popen(self.link_texts[self.current_idx])
            except:
                pass
        elif lnk["kind"] == fitz.LINK_NAMED:
            if lnk["name"] == "FirstPage":
                self.TextToPage.Value = "1"
            elif lnk["name"] == "LastPage":
                self.TextToPage.Value = str(len(self.doc))
            elif lnk["name"] == "NextPage":
                self.TextToPage.Value = str(int(self.TextToPage.Value) + 1)
            elif lnk["name"] == "PrevPage":
                self.TextToPage.Value = str(int(self.TextToPage.Value) - 1)
            self.GotoPage(evt)
        evt.Skip()
        return

    def move_mouse(self, evt):  # show hand if in a rectangle
        if not self.links.Value:  # do not process links
            evt.Skip()
            return
        if len(self.link_rects) == 0:
            evt.Skip()
            return
        pos = evt.GetPosition()
        self.current_idx = self.cursor_in_link(pos)  # get cursor link rect

        if self.current_idx >= 0:  # if in a hot area
            self.PDFimage.SetCursor(cursor_hand)
            if phoenix:
                self.PDFimage.SetToolTip(self.link_texts[self.current_idx])
            else:
                self.PDFimage.SetToolTipString(self.link_texts[self.current_idx])
        else:
            self.PDFimage.SetCursor(cursor_norm)
            self.PDFimage.UnsetToolTip()

        evt.Skip()
        return

    def OnMouseWheel(self, evt):
        # process wheel as paging operations
        d = evt.GetWheelRotation()  # int indicating direction
        if d < 0:
            self.NextPage(evt)
        elif d > 0:
            self.PreviousPage(evt)
        return

    def NextPage(self, event):  # means: page forward
        page = self.current_page + 1  # current page + 1
        page = min(page, self.no_pages)  # cannot go beyond last page
        self.TextToPage.Value = str(page)  # put target page# in screen
        self.current_page = page
        self.NeuesImage(page, 0)  # refresh the layout
        event.Skip()

    def PreviousPage(self, event):  # means: page back
        page = self.current_page - 1  # current page - 1
        page = max(page, 1)  # cannot go before page 1
        self.TextToPage.Value = str(page)  # put target page# in screen
        self.current_page = page
        self.NeuesImage(page, 0)
        event.Skip()

    def GotoPage(self, event):  # means: go to page number
        page = self.current_page  # get page# from screen
        page = min(page, self.no_pages)  # cannot go beyond last page
        page = max(page, 1)  # cannot go before page 1
        self.TextToPage.Value = str(page)  # make sure it's on the screen
        self.current_page = page
        self.NeuesImage(page, 0)
        event.Skip()

    # ==============================================================================
    # Read / render a PDF page. Parameters are: pdf = document, page = page#
    # ==============================================================================
    def NeuesImage(self, page, flag1):
        # if page == self.last_page:
        #    return
        self.PDFimage.SetCursor(cursor_norm)
        self.PDFimage.UnsetToolTip()
        self.last_page = page
        self.link_rects = []
        self.link_texts = []
        bitmap = self.pdf_show(page, flag1)  # read page image

        if self.links.Value and len(self.current_lnks) > 0:  # show links?
            self.draw_links(bitmap, page)  # modify the bitmap
        self.PDFimage.SetBitmap(bitmap)  # put it in screen
        self.szr10.Fit(self)
        self.SetSizer(self.szr10)
        self.Layout()
        #self.show()
        print("Update---")
        # center dialog on screen
        # self.Centre(wx.BOTH)
        # image may be truncated, so we need to recalculate hot areas
        if len(self.current_lnks) > 0:
            isize = self.PDFimage.Size
            bsize = self.PDFimage.Bitmap.Size
            dis_x = (bsize[0] - isize[0]) / 2.
            dis_y = (bsize[1] - isize[1]) / 2.
            zoom_w = float(bsize[0]) / float(self.pg_ir.width)
            zoom_h = float(bsize[1]) / float(self.pg_ir.height)
            for l in self.current_lnks:
                r = l["from"]
                wx_r = wx.Rect(int(r.x0 * zoom_w - dis_x),
                               int(r.y0 * zoom_h) - dis_y,
                               int(r.width * zoom_w),
                               int(r.height * zoom_h))
                self.link_rects.append(wx_r)

        return

    def cursor_in_link(self, pos):
        for i, r in enumerate(self.link_rects):
            if r.Contains(pos):
                return i
        return -1

    def draw_links(self, bmp, pno):
        dc = wx.MemoryDC()
        dc.SelectObject(bmp)
        dc.SetPen(wx.Pen("BLUE", width=1))
        dc.SetBrush(wx.Brush("BLUE", style=wx.BRUSHSTYLE_TRANSPARENT))
        pg_w = self.pg_ir.x1 - self.pg_ir.x0
        pg_h = self.pg_ir.y1 - self.pg_ir.y0
        zoom_w = float(bmp.Size[0]) / float(pg_w)
        zoom_h = float(bmp.Size[1]) / float(pg_h)
        for lnk in self.current_lnks:
            r = lnk["from"].irect
            wx_r = wx.Rect(int(r.x0 * zoom_w),
                           int(r.y0 * zoom_h),
                           int(r.width * zoom_w),
                           int(r.height * zoom_h))
            dc.DrawRectangle(wx_r[0], wx_r[1], wx_r[2] + 1, wx_r[3] + 1)
            if lnk["kind"] == fitz.LINK_GOTO:
                txt = "page " + str(lnk["page"] + 1)
            elif lnk["kind"] == fitz.LINK_GOTOR:
                txt = lnk["file"]
            elif lnk["kind"] == fitz.LINK_URI:
                txt = lnk["uri"]
            else:
                txt = "unkown destination"
            self.link_texts.append(txt)
        dc.SelectObject(wx.NullBitmap)
        dc = None
        return

    def pdf_show(self, pg_nr, flag1):
        pno = int(pg_nr) - 1
        if flag1 == 1:
            pass
        elif flag1 == 0:
            # if self.dl_array[pno] == 0:
            # self.dl_array[pno]=None
            self.doc.close()
            self.doc = fitz.open(filename)  # create Document object
            self.no_pages = len(self.doc)
            # self.doc1 = fitz.open(filename)
            self.doc1.close()
            self.doc.select([pno])
            self.doc.save("page_.pdf", garbage=3)
            self.doc.close()
            self.doc1 = fitz.open("page_.pdf")
            self.doc = fitz.open(filename)  # create Document object

        self.dl_array[pno] = self.doc1[0].getDisplayList()
        dl = self.dl_array[pno]
        rect = dl.rect  # the page rectangle
        pix = None
        if 0 <= self.currentZoom <= 33:
            self.matrix = fitz.Matrix(0.8, 0.8)
            pix = dl.getPixmap(matrix=self.matrix, alpha=False)
        elif 33 < self.currentZoom <= 66:
            self.matrix = fitz.Matrix(1.5, 1.5)            # upper Point
            if 1:
                mr = rect.tr + (rect.br - rect.tr) * 0.5  # its middle point
                clip = fitz.Rect(rect.tl, mr)  # the area we want
                pix = dl.getPixmap(matrix=self.matrix, alpha=False, clip=clip)
            else:  # bottom point
                ml = rect.tl + (rect.bl - rect.tl) * 0.5
                clip = fitz.Rect(ml, rect.br)  # the area we want
                pix = dl.getPixmap(matrix=self.matrix, alpha=False, clip=clip)

        elif 66 < self.currentZoom <= 100:
            self.matrix = fitz.Matrix(1.5, 1.5)
            if 1:
                mr = rect.tr + (rect.br - rect.tr) * 0.3
                clip = fitz.Rect(rect.tl, mr)  # the area we want
                pix = dl.getPixmap(matrix=self.matrix, alpha=False, clip=clip)
            elif 2:
                mdl = rect.tl + (rect.bl - rect.tl) * 0.3  # its middle point
                mdr = rect.br - (rect.br - rect.tr) * 0.3  # its middle point
                clip = fitz.Rect(mdl, mdr)  # the area we want
                pix = dl.getPixmap(matrix=self.matrix, alpha=False, clip=clip)
            else:
                mdr = rect.bl - (rect.bl - rect.tl) * 0.3  # its middle point
                clip = fitz.Rect(mdr, rect.br)  # the area we want
                pix = dl.getPixmap(matrix=self.matrix, alpha=False, clip=clip)

        # self.matrix = fitz.Matrix(0.8, 0.8)
        # pix = dl.getPixmap(matrix=self.matrix, alpha=False)
        #self.matrix = fitz.Matrix(1.5, 1.5)  # upper Point
        #pix = dl.getPixmap(matrix=self.matrix, alpha=False)

        if pix:
            bmp = bmp_buffer(pix.w, pix.h, pix.samples)
            r = dl.rect
            paper = FindFit(r.x1, r.y1)
            self.paperform.Label = "Page format: " + paper
            if self.links.Value:
                self.current_lnks = self.doc1[0].getLinks()
                self.pg_ir = dl.rect.irect
            pix = None
            self.dl_array[pno] = None
            return bmp

    def decrypt_doc(self):
        # let user enter document password
        pw = None
        dlg = wx.TextEntryDialog(self, 'Please enter password below:',
                                 'Document needs password to open', '',
                                 style=wx.TextEntryDialogStyle | wx.TE_PASSWORD)
        while pw is None:
            rc = dlg.ShowModal()
            if rc == wx.ID_OK:
                pw = str(dlg.GetValue().encode("utf-8"))
                self.doc.authenticate(pw)
            else:
                return
            if self.doc.isEncrypted:
                pw = None
                dlg.SetTitle("Wrong password. Enter correct one or cancel.")
        return


# ==============================================================================
# main program
# ------------------------------------------------------------------------------
# Show a standard FileSelect dialog to choose a file for display
# ==============================================================================
# Wildcard: offer all supported filetypes for display
wild = "*.pdf;*.xps;*.oxps;*.epub;*.cbz;*.fb2"

# ==============================================================================
# define the file selection dialog
# ==============================================================================
dlg = wx.FileDialog(None, message="Choose a file to display",
                    wildcard=wild, style=wx.FD_OPEN | wx.FD_CHANGE_DIR)

# We got a file only when one was selected and OK pressed
if dlg.ShowModal() == wx.ID_OK:
    # This returns a Python list of selected files (we only have one though)
    filename = dlg.GetPath()
else:
    filename = None

# destroy this dialog
dlg.Destroy()

# only continue if we have a filename
if filename:
    # create the dialog
    dlg = PDFdisplay(None, filename)
    # show it - this will only return for final housekeeping
    rc = dlg.ShowModal()
    dlg.Destroy()

app = None
try:
    engine.endLoop()
    engine.stop()
except:
    raise SystemExit(__file__ + " needs pyttx3")




'''
        if 0 <= self.currentZoom <= 33:
            self.matrix = fitz.Matrix(0.8, 0.8)
            pix = dl.getPixmap(matrix=self.matrix, alpha=False)
        elif 33 < self.currentZoom <= 66:
            self.matrix = fitz.Matrix(1.5, 1.5)  # upper Point
            if 1:
                mr = rect.tr + (rect.br - rect.tr) * 0.5  # its middle point
                clip = fitz.Rect(rect.tl, mr)  # the area we want
                pix = dl.getPixmap(matrix=self.matrix, alpha=False, clip=clip)
            else:  # bottom point
                ml = rect.tl + (rect.bl - rect.tl) * 0.5
                clip = fitz.Rect(ml, rect.br)  # the area we want
                pix = dl.getPixmap(matrix=self.matrix, alpha=False, clip=clip)

        elif 66 < self.currentZoom <= 100:
            self.matrix = fitz.Matrix(1.5, 1.5)
            if 1:
                mr = rect.tr + (rect.br - rect.tr) * 0.3
                clip = fitz.Rect(rect.tl, mr)  # the area we want
                pix = dl.getPixmap(matrix=self.matrix, alpha=False, clip=clip)
            elif 2:
                mdl = rect.tl + (rect.bl - rect.tl) * 0.3  # its middle point
                mdr = rect.br - (rect.br - rect.tr) * 0.3  # its middle point
                clip = fitz.Rect(mdl, mdr)  # the area we want
                pix = dl.getPixmap(matrix=self.matrix, alpha=False, clip=clip)
            else:
                mdr = rect.bl - (rect.bl - rect.tl) * 0.3  # its middle point
                clip = fitz.Rect(mdr, rect.br)  # the area we want
                pix = dl.getPixmap(matrix=self.matrix, alpha=False, clip=clip)
'''

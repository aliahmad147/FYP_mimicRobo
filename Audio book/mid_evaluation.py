# !/usr/bin/python
# -*- coding: utf-8 -*-

"""
@created: 2019-9-23 13:40:00
@author: Ali Ahmad Mansoor
"""
import sys
import pandas as pd
from pdf2image import convert_from_path
print("Python:", sys.version)
#import matplotlib.pyplot as plt
#import cv2

import pyttsx3


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



# abbreviations to get rid of those long pesky names ...
# ==============================================================================
# Define our dialog as a subclass of wx.Dialog.
# Only special thing is, that we are being invoked with a filename ...
# ==============================================================================
class PDFdisplay(wx.Dialog):
    def __init__(self, parent, filename):
        self.filename = filename
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
        self.SetTitle(self.Title + "Audio Book")
        self.SetBackgroundColour(wx.Colour(240, 230, 140))
        self.currentZoom = 0

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

        self.doc1.save("page_image.pdf", garbage=3)
        self.doc1.close()
        try:
            pages = convert_from_path('C:/Users/Ahmad/PycharmProjects/GUI_test/page_image.pdf', 200, single_file=True)
            pages[0].save('file5.jpg', 'JPEG')
            # pages[0].show()
        except:
            print("Error in saving image")

        self.doc1 = fitz.open("page_.pdf")
        self.doc = fitz.open(filename)  # create Document object

        self.engine = pyttsx3.init()
        rate = self.engine.getProperty('rate')
        self.engine.setProperty('rate', 150)

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
        self.currentspeaker=0
        self.SpeakerArray=["HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0","HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0","HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-GB_HAZEL_11.0"]

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
        self.ButtonNextW = wx.Button(self, wx.ID_ANY, u"Start",
                                     defPos, defSiz, wx.BU_EXACTFIT)

        # forward button
        self.ButtonNext = wx.Button(self, wx.ID_ANY, u"forw",
                                    defPos, defSiz, wx.BU_EXACTFIT)

        # backward button
        self.ButtonPrevious = wx.Button(self, wx.ID_ANY, u"back",
                                        defPos, defSiz, wx.BU_EXACTFIT)
        self.Buttonspeak = wx.Button(self, wx.ID_ANY, u"generate",
                                     defPos, defSiz, wx.BU_EXACTFIT)

        self.ButtonStop = wx.Button(self, wx.ID_ANY, u"stop",
                                    defPos, defSiz, wx.BU_EXACTFIT)
        self.ChangeSpeaker = wx.Button(self, wx.ID_ANY, u"Change Speaker",
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
        szr20.Add(self.ChangeSpeaker, 0, wx.ALL, 5)

        szr20.Add(self.TextToPage, 0, wx.ALL, 5)
        szr20.Add(self.statPageMax, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        szr20.Add(self.links, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        szr20.Add(self.paperform, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        # sizer ready, represents top dialog line
        self.szr10.Add(szr20, 0, wx.EXPAND, 5)

        # szr30 = wx.BoxSizer(wx.HORIZONTAL)
        # szr40 = wx.BoxSizer(wx.VERTICAL)
        # szr30.Add(szr40,1, wx.EXPAND, 5)

        # self.szr10.Add(szr30, 0, wx.EXPAND, 5)
        # main sizer now ready - request final size & layout adjustments
        self.szr10.Fit(self)
        self.SetSizer(self.szr10)
        self.Layout()
        # center dialog on screen
        self.Centre(wx.BOTH)

        # Bind buttons and fields to event handlers
        self.ButtonNext.Bind(wx.EVT_BUTTON, self.NextPage)
        self.ChangeSpeaker.Bind(wx.EVT_BUTTON, self.change_speaker)

        self.ButtonPrevious.Bind(wx.EVT_BUTTON, self.PreviousPage)
        self.ButtonNextW.Bind(wx.EVT_BUTTON, self.highlight)
        self.Buttonspeak.Bind(wx.EVT_BUTTON, self.PreProcess)
        self.ButtonStop.Bind(wx.EVT_BUTTON, self.Stop_running)

        self.TextToPage.Bind(wx.EVT_TEXT_ENTER, self.GotoPage)


    def distance(self, point1, point2):
        if (point1 and point2):
            return point1[0] - point2[0], point1[1] - point2[1]

    def Not_Equal(self, point1, point2):
        if (point1 and point2):
            if (point1[0] == point2[0] and point1[1] == point2[1]):
                return 0
            else:
                return point1[1] - point2[1]

    def change_speaker(self,event):
        try:
            if self.currentspeaker==0:
                self.currentspeaker=1
                self.engine.setProperty('voice', self.SpeakerArray[self.currentspeaker])
            elif self.currentspeaker==1:
                self.currentspeaker=2
                self.engine.setProperty('voice', self.SpeakerArray[self.currentspeaker])
            elif self.currentspeaker==2:
                self.currentspeaker=0
                self.engine.setProperty('voice', self.SpeakerArray[self.currentspeaker])
        except:
            print("Cannot change")
        print("Change Speaker")
        return
    def Stop_running(self, event):
        print("flag function")
        self.flag_OnOff = False
        # try:
        #     self.engine.runAndWait()
        #     self.engine.stop()
        # except:
        #     print("Error")
        # self.engine.setProperty('voice',"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0")
        # self.engine = pyttsx3.init()
        # rate = self.engine.getProperty('rate')
        # self.engine.setProperty('rate', 150)

    def Speak(self, line):
        print("=> ", line)
        try:
            self.engine.say(line)
            self.engine.runAndWait()
            self.engine.stop()
        except:
            self.engine.stop()
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
        #self.Speak(word)
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
        self.file_data = pd.read_csv("text_instances_page.csv")
        page = 0

        word = "Start"
        for i in range(len(self.file_data.location)):
            self.NeuesImage(self.current_page, 0)
            event.Skip()

            if self.currentword < len(self.file_data.location):
                element = self.file_data.location[self.currentword]
                if word!="Start":
                    self.Speak(word)
                word = self.file_data.line[self.currentword]
                try:
                    print("1-")
                    element = element.replace(')', '')
                    element = element.replace('(', '')
                    element = element.replace(' ', '')
                    Arr = element.split(',')
                    arr2 = [float(i) for i in Arr]
                    #print(arr2)
                    print("2-")
                    highlight = self.doc1[page].addHighlightAnnot(arr2)
                    print("3-")
                    self.NeuesImage(self.current_page, 1)
                    event.Skip()
                    print("4-")
                    if self.flag_OnOff == False:
                        self.flag_OnOff = True
                        break
                    # self.wait_for(1000)
                    #  sleep(1.5)
                    self.currentword += 1
                    # #self.wait_for(3000)
                    print("!")

                except:
                    print("Exception...")


    def PreProcess(self, event):
        df1 = pd.DataFrame({"line": [], "location": []})
        page = 0
        for block in self.doc1[page].getTextBlocks(flags=None):
            text1 = block[4]
            #text1 = text1.replace('-', "")
            print (text1)
            arr1 = text1.split("\n")

            if (len(arr1) > 1):
                for line in arr1:
                    text_inst = self.doc1[page].searchFor(line)
                    if (text_inst):
                        for inst in text_inst:

                            print(inst[0], inst[1],inst[2], inst[3])
                            print(inst)
                            print ([line])
                            df2 = pd.DataFrame(
                                {"line": [line], "location": [(inst[0], inst[1],inst[2], inst[3])]})
                            df1 = df1.append(df2, ignore_index=True)

            else:
                text_inst = self.doc1[page].searchFor(arr1[0])
                if (text_inst):
                    for inst in text_inst:
                        print(inst[0], inst[1], inst[2], inst[3])
                        print(inst)
                        df2 = pd.DataFrame(
                            {"line": [arr1[0]], "location": [(inst[0], inst[1], inst[2], inst[3])]})
                        df1 = df1.append(df2, ignore_index=True)
        df1.to_csv('text_instances_page.csv', index=False)
        print("Done")
    def OnMouseWheel(self, evt):
        # process wheel as paging operations
        d = evt.GetWheelRotation()  # int indicating direction
        if d < 0:
            self.NextPage(evt)
        elif d > 0:
            self.PreviousPage(evt)
        return

    def NextPage(self, event):  # means: page forward
        self.currentword=0
        page = self.current_page + 1  # current page + 1
        page = min(page,self.doc.pageCount)  # cannot go beyond last page
        self.TextToPage.Value = str(page)  # put target page# in screen
        self.current_page = page
        self.NeuesImage(page, 2)  # refresh the layout
        event.Skip()
        print("Forward")

    def PreviousPage(self, event):  # means: page back
        self.currentword=0
        page = self.current_page-1   # current page - 1
        page = max(page, 1)  # cannot go before page 1
        self.TextToPage.Value = str(page)  # put target page# in screen
        self.current_page = page
        self.NeuesImage(page, 2)
        event.Skip()
        print("Previous")

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
        self.last_page = page
        self.link_rects = []
        self.link_texts = []
        self.pdf_show(page, flag1)  # read page image
        #self.szr10.Fit(self)
        #self.SetSizer(self.szr10)
        self.Layout()
        return

    def pdf_show(self, pg_nr, flag1):
        pno = int(pg_nr)-1
        if flag1 == 1:
            pass
        elif flag1 == 0:
            # if self.dl_array[pno] == 0:
            # self.dl_array[pno]=None
            self.doc.close()
            self.doc = fitz.open(self.filename)  # create Document object
            self.no_pages = len(self.doc)
            # self.doc1 = fitz.open(filename)
            self.doc.select([pno])
            self.doc1.save("page_image.pdf", garbage=3)
            self.doc1.close()
            #self.doc.save("page_.pdf", garbage=3)
            #self.doc.close()

            try:
                pages = convert_from_path('C:/Users/Ahmad/PycharmProjects/GUI_test/page_image.pdf', 200, single_file=True)
                pages[0].save('file5.jpg', 'JPEG')
                #pages[0].show()
            except:
                print("Error in saving image")
            self.doc.save("page_.pdf", garbage=3)
            self.doc.close()

            self.doc1 = fitz.open("page_.pdf")
            self.doc = fitz.open(self.filename)  # create Document object
        elif flag1==2:
            self.doc.close()
            self.doc1.close()
            self.doc = fitz.open(self.filename)  # create Document object
            self.no_pages = len(self.doc)
            # self.doc1 = fitz.open(filename)
            self.doc.select([pno])
            self.doc.save("page_.pdf", garbage=3)
            self.doc.close()

            self.doc1 = fitz.open("page_.pdf")

            self.doc1.save("page_image.pdf", garbage=3)
            self.doc1.close()
            # self.doc.save("page_.pdf", garbage=3)
            # self.doc.close()

            try:
                pages = convert_from_path('C:/Users/Ahmad/PycharmProjects/GUI_test/page_image.pdf', 200,
                                          single_file=True)
                pages[0].save('file5.jpg', 'JPEG')
                # pages[0].show()
            except:
                print("Error in saving image")

            self.doc1 = fitz.open("page_.pdf")
            self.doc = fitz.open(self.filename)  # create Document object

        return

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

def run_code():
    # Wildcard: offer all supported filetypes for display
    wild = "*.pdf"

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
run_code()


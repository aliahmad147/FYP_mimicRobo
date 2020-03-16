import pandas as pd
import pysrt
import srt as srt

from pydub import AudioSegment

import re
from datetime import datetime
i=0
file_name="audio"
song = AudioSegment.from_mp3(file_name + '.wav')
with open('srt_file.srt', "r") as f:
        srtText = f.read()
        #subs = list(srt.parse(srtText))
        subs = []
        # re.sub(pattern, repl, string, count=0, flags=0)¶
        for s in srtText.split('\n\n'):
            list1 = s.split('\n')
            if len(list1) >= 3:
                split1 = list1[1].split(' --> ')
                if len(split1)>=2:
                    print (split1[0].strip(),"_4_",split1[1].strip())
                    #print("line",list1[2:len(list1)])
                    print (' '.join(j for j in list1[2:len(list1)]))
                    dt_obj = datetime.strptime(split1[0].strip(),
                                               '%H:%M:%S,%f')
                    time = dt_obj.time()
                    miliseconds1 = int(3600000 * int(str(time.hour)) + 60000 * int(str(time.minute)) + 1000 * int(
                        str(time.second)) )
                    print(miliseconds1)
                    #+ int(str(time.microsecond)) + int(str(time.microsecond))

                    dt_obj = datetime.strptime(split1[1].strip(),
                                               '%H:%M:%S,%f')
                    time = dt_obj.time()
                    miliseconds2 = int(3600000 * int(str(time.hour)) + 60000 * int(str(time.minute)) + 1000 * int(
                        str(time.second)))
                    print (miliseconds2)
                    song = AudioSegment.from_mp3(file_name + '.wav')
                    extract = song[miliseconds1:miliseconds2]
                    # Saving
                    extract.export('extract'+str(i), format="wav")
                    i+=1
            else:
                print("Error")
                print(s)
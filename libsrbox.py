"""
This file is part of OpenSesame.

OpenSesame is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenSesame is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenSesame.  If not, see <http://www.gnu.org/licenses/>.




NOAH CHANGE LOG
added check_buffer
modified get_button_press to allow escape out, and exit if button is pressed
modified stop() to not flush buffers


"""

from libopensesame import debug, exceptions
import serial
import os
import warnings
import math

class libsrbox:

        # The PST sr box only supports five buttons, but some of the VU boxes use
        # higher button numbers
        BUTTON1 = int('11111110', 2)
        BUTTON2 = int('11111101', 2)
        BUTTON3 = int('11111011', 2)
        BUTTON4 = int('11110111', 2)
        BUTTON5 = int('11101111', 2)
        BUTTON6 = int('11011111', 2)
        BUTTON7 = int('10111111', 2)
        BUTTON8 = int('01111111', 2)

        def __init__(self, experiment, dev=None):

                """<DOC>
                Constructor. Connects to the SR Box.

                Arguments:
                experiment -- Opensesame experiment.

                Keywords arguments:
                dev -- The srbox device port or None for auto-detect (default=None).
                </DOC>"""

                self.experiment = experiment
                self._srbox = None

                #attributes for check_buffer
                self.buttonsDown=[0]*8
                self.buttonDownDurations=[0]*8
                self.buttonUpDurations=[0]*8
                self.tLastFlush=0
                self.timeout=200
                self.buttonList=range(1,9)

                # If a device has been specified, use it
                if dev not in (None, "", "autodetect"):
                        try:
                                self._srbox = serial.Serial(dev, timeout=0, baudrate=19200)
                        except Exception as e:
                                raise exceptions.runtime_error( \
                                        "Failed to open device port '%s' in libsrbox: '%s'" \
                                        % (dev, e))

                else:
                        # Else determine the common name of the serial devices on the
                        # platform and find the first accessible device. On Windows,
                        # devices are labeled COM[X], on Linux there are labeled /dev/tty[X]
                        if os.name == "nt":
                                for i in range(255):
                                        try:
                                                dev = "COM%d" % i
                                                self._srbox = serial.Serial(dev, timeout=0, \
                                                        baudrate=19200)
                                                break
                                        except Exception as e:
                                                self._srbox = None
                                                pass

                        elif os.name == "posix":
                                for path in os.listdir("/dev"):
                                        if path[:3] == "tty":
                                                try:
                                                        dev = "/dev/%s" % path
                                                        self._srbox = serial.Serial(dev, timeout=0, \
                                                                baudrate=19200)
                                                        break
                                                except Exception as e:
                                                        self._srbox = None
                                                        pass
                        else:
                                raise exceptions.runtime_error( \
                                        "libsrbox does not know how to auto-detect the SR Box on your platform. Please specify a device.")

                if self._srbox == None:
                        raise exceptions.runtime_error( \
                                "libsrbox failed to auto-detect an SR Box. Please specify a device.")
                debug.msg("using device %s" % dev)
                # Turn off all lights
                if self._srbox != None:
                        self._srbox.write('\x64')

        def send(self, ch):

                """<DOC>
                Sends a single character.

                Arguments:
                ch -- The character to send.
                </DOC>"""

                self._srbox.write(ch)

        def start(self):

                """<DOC>
                Turns on sending mode, to start giving output.

                Example:
                >>> exp.srbox.start()
                >>> timestamp, buttonsPressed = exp.srbox.get_button_press(allowed_buttons=[1,2])
                >>> if 1 in buttonsPressed:
                >>>             print 'Button 1 was pressed!'
                >>> exp.srbox.stop()
                </DOC>"""

                # Write the start byte
                self._srbox.write('\xA0')
                self._srbox.flushOutput()
                self._srbox.flushInput()

        def stop(self):

                """<DOC>
                Turns off sending mode, to stop giving output.

                Example:
                >>> exp.srbox.start()
                >>> timestamp, buttonsPressed = exp.srbox.get_button_press(allowed_buttons=[1,2])
                >>> if 1 in buttonsPressed:
                >>>             print 'Button 1 was pressed!'
                >>> exp.srbox.stop()
                </DOC>"""

                # Write the stop byte and flush the input
                self._srbox.write('\x20')
                #self._srbox.flushOutput()
                #self._srbox.flushInput()

        def get_button_press(self, allowed_buttons=None, timeout=None):

                """<DOC>
                Gets a button press from the SR box.

                Keywords arguments:
                allowed_buttons -- A list of buttons that are accepted or None to accept #
                                                   all buttons. Valid buttons are integers 1 through 8. #
                                                   (default=None)
                timeout -- A timeout value or None for no timeout. (default=None)

                Returns:
                A timestamp, buttonsPressed tuple. The buttonsPressed consists of a list of #
                button numbers.

                Example:
                >>> exp.srbox.start()
                >>> timestamp, buttonsPressed = exp.srbox.get_button_press(allowed_buttons=[1,2])
                >>> if 1 in buttonsPressed:
                >>>             print 'Button 1 was pressed!'
                >>> exp.srbox.stop()
                </DOC>"""
        
                c = self.experiment.time()
                t = c
                from openexp.keyboard import keyboard

                kb=keyboard(self.experiment,keylist=['escape'],timeout=1)

                while timeout == None or t - c < timeout:

                        key,resTime=kb.get_key()
                        
                        j = self._srbox.read(1)
                        
                        t = self.experiment.time()
                        if j != "" and j != '\x00':
                                k = ord(j)

                                if k != 0:
                                        l = []
                                        if k | self.BUTTON1 == 255 and (allowed_buttons == None or \
                                                1 in allowed_buttons):
                                                l.append(1)
                                        if k | self.BUTTON2 == 255 and (allowed_buttons == None or \
                                                2 in allowed_buttons):
                                                l.append(2)
                                        if k | self.BUTTON3 == 255 and (allowed_buttons == None or \
                                                3 in allowed_buttons):
                                                l.append(3)
                                        if k | self.BUTTON4 == 255 and (allowed_buttons == None or \
                                                4 in allowed_buttons):
                                                l.append(4)
                                        if k | self.BUTTON5 == 255 and (allowed_buttons == None or \
                                                5 in allowed_buttons):
                                                l.append(5)
                                        if k | self.BUTTON6 == 255 and (allowed_buttons == None or \
                                                6 in allowed_buttons):
                                                l.append(6)
                                        if k | self.BUTTON7 == 255 and (allowed_buttons == None or \
                                                7 in allowed_buttons):
                                                l.append(7)
                                        if k | self.BUTTON8 == 255 and (allowed_buttons == None or \
                                                8 in allowed_buttons):
                                                l.append(8)
                                        if l != []:
                                                return [l, t]
                return None, t
        
        def check_buffer(self, allowed_buttons):
                import warnings
                from openexp.keyboard import keyboard
                kb=keyboard(self.experiment,keylist=['escape'],timeout=1)
                key,resTime=kb.get_key()#allow escape out

                checkTime=self.experiment.time()
                if self._srbox.inWaiting()>0:
                        tPerEntry=(float(checkTime-self.tLastFlush)/self._srbox.inWaiting()) # milliseconds per entry in this check
                else:
                        tPerEntry=99
                        
                timeout=10; #timeout in seconds; prevents repeats
                
                        
                dataList=[]
                entryNum=0
                response=0
                responseTime=-99
                #allButtons=range(1,9)
                #buttonsPressed=[] #list of buttons pressed in a single timestep
                #loop over input buffer
                if self._srbox.inWaiting()==4096:
                    warnings.warn('BUFFER FULL; CHECK MORE FREQUENTLY')

                
                bufferCopy, new_tLastFlush=self.copy_buffer()
                
                for index,entry in enumerate(bufferCopy):
                                   
                        entryInt=ord(entry)
                        
                        entryNum=index+1

                        buttonsPressed = []
                        if entryInt>0:                            
                            
                            if entryInt | self.BUTTON1 == 255 and (allowed_buttons == None or \
                                    1 in allowed_buttons):
                                    buttonsPressed.append(1)
                            if entryInt | self.BUTTON2 == 255 and (allowed_buttons == None or \
                                    2 in allowed_buttons):
                                    buttonsPressed.append(2)
                            if entryInt | self.BUTTON3 == 255 and (allowed_buttons == None or \
                                    3 in allowed_buttons):
                                    buttonsPressed.append(3)
                            if entryInt | self.BUTTON4 == 255 and (allowed_buttons == None or \
                                    4 in allowed_buttons):
                                    buttonsPressed.append(4)
                            if entryInt | self.BUTTON5 == 255 and (allowed_buttons == None or \
                                    5 in allowed_buttons):
                                    buttonsPressed.append(5)
                            if entryInt | self.BUTTON6 == 255 and (allowed_buttons == None or \
                                    6 in allowed_buttons):
                                    buttonsPressed.append(6)
                            if entryInt | self.BUTTON7 == 255 and (allowed_buttons == None or \
                                    7 in allowed_buttons):
                                    buttonsPressed.append(7)
                            if entryInt | self.BUTTON8 == 255 and (allowed_buttons == None or \
                                    8 in allowed_buttons):
                                    buttonsPressed.append(8)

                        for button in allowed_buttons: #check every button          
                            
                            if button in buttonsPressed: #if the button was pressed on this timepoint
                                if self.buttonsDown[button-1]==0: #if button was up
                                    self.buttonsDown[button-1]=1 #now its down
                                    self.buttonDownDurations[button-1]=tPerEntry
                                    
                                    if self.buttonUpDurations[button-1] > self.timeout:
                                        dataList.append([button, round(self.tLastFlush+entryNum*tPerEntry)])


                                elif self.buttonsDown[button-1]==1:
                                    self.buttonDownDurations[button-1]+=tPerEntry
        

                            elif button not in buttonsPressed:
                                if self.buttonsDown[button-1]==1:
                                    self.buttonsDown[button-1]=0
                                    self.buttonUpDurations[button-1]=tPerEntry

                                elif self.buttonsDown[button-1]==0:
                                    self.buttonUpDurations[button-1]+=tPerEntry
                                    
                self.tLastFlush=new_tLastFlush
                return dataList          

        def copy_buffer(self):
         
                bufferCopy=self._srbox.read(self._srbox.inWaiting())
                flushTime=self.experiment.time() #put before or after read? does it matter?
                return bufferCopy, flushTime               
                
        def close(self):

                """<DOC> TODO
                Closes the connection to the srbox. This is (sometimes?) required in #
                order to re-use the SR Box in the same session of OpenSesame.
                </DOC>"""

                self._srbox.close()




'''
                        for button in buttonsPressed: #for every button pressed in a single timepoint

                            if button!=seen:                    
                                seen=button;
                                
                                if button!=0 and entryNum > timeoutStart+timeout*bps: #prevent repeats (problem for separate buttons?)

                                    if response == 0 and button in watchFor: #if looking for a response, take the first one
                                        response=button
                                        responseTime=tLastFlush+entryNum/bps
                                        
                                    
                                    timeoutStart=entryNum
                                    timestamp=tLastFlush+entryNum/bps
                                    dataList.append([seen,timestamp])
'''

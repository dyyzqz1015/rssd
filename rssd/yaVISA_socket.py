#####################################################################
### Rohde & Schwarz Automation for demonstration use.
###
### Purpose: Yet(Just) Another VISA wrapper
### Author:  Martin C Lim
### Date:    2017.09.01
### Requird: python -m pip install pyvisa
### Descrip: Wrapper for common VISA commands
###          properties for: Make; Model; Version; IDN; last error
###          logSCPI --> file for 
#####################################################################
import time
import rssd.FileIO                        #pylint: disable=E0611,E0401
import socket

class jaVisa(object):
   ### Rohde & Schwarz VISA Class
   ### Instrument Common functions. 
   def __init__(self):
      self.dataIDN = ""
      self.filenm  = ""
      self.Make    = ""
      self.Model   = ""
      self.Device  = ""
      self.Version = ""
      self.prnty   = 1
      self.Ofile   = ""
      pass
   
   def delay(self,sec):
      time.sleep(sec)

   def jav_Clear(self):
      #self.K2.clear()
      pass

   def jav_Close(self):
      try:
         errList = self.jav_ClrErr()
         self.K2.close()
         return errList
      except:
         pass

   def jav_ClrErr(self):
      ErrList = []
      while True:
         RdStr = self.query("SYST:ERR?").strip()
         ErrList.append(RdStr)
         RdStrSplit = RdStr.split(',')
         if RdStr == "<notRead>": break      #No readstring
         if RdStrSplit[0] == "0": break      #Read 0 error:R&S
         if RdStrSplit[0] == "+0": break     #Read 0 error:Other
         self.dLastErr = RdStr
         print("jav_ClrErr: %s-->%s"%(self.Model,RdStr))
      return ErrList 
         
   def jav_Error(self):
      RdStr = self.query("SYST:ERR?").strip().split(',')
      return RdStr

   def jav_IDN(self,prnt=1):
      self.dataIDN = "Temp"                  #Temp for self.query
      self.dataIDN = self.query("*IDN?").strip()
      if self.dataIDN != "<notRead>":        #Data Returned?
         IDNStr = self.dataIDN.split(',')
         self.Make    = IDNStr[0]
         self.Model   = IDNStr[1]
         self.Device  = IDNStr[2]
         self.Version = IDNStr[3]
      else:
         self.dataIDN = ""                   #Reset if not read
      if prnt==1:
         print('jav_IDN   : %s'%(self.dataIDN))
      return self.dataIDN
            
   def jav_OPC_Wait(self, InCMD):
      start_time = time.time()
      self.write("*ESE 1")		               #Event Status Enable
      self.write("*SRE 32")		            #ServiceReqEnable-Bit5:Std Event
      self.write(InCMD + ";*OPC")	         #Initiate Read.  *OPC will trigger ESR
      #print ('   OPC Wait: ' +InCMD)
      read = "0"
      while (int(read) & 1) != 1:            #Loop until done
         try:
            read = self.query("*ESR?").strip()#Poll EventStatReg-Bit0:Op Complete  (STB?)
         except:
            print("jav_OPCWai:*ESR? Error")
         time.sleep(0.5)
         delta = (time.time() - start_time)
         if delta > 300:
            print("jav_OPCWai: timeout")
            break
      print('jav_OPCWai: %0.2fsec'%(delta))
      return delta
   
   def jav_Open(self, sIPAddr, fily='',prnt=1):
      #*****************************************************************
      #*** Open raw socket Connection
      #*****************************************************************
      self.K2 = socket.socket()
      try:
         #s.setttimeout(1)
         self.K2.connect((sIPAddr,5025))
         self.K2.settimeout(1)
         self.jav_IDN(prnt)
         try:  # Try to write file
            f=open(fily,'a')
            f.write(self.dataIDN + "\n")
            f.close()
         except:
            pass
         self.jav_ClrErr()
      except:
         print ('jav_OpnErr: ' + sIPAddr)
         self.K2 = 'NoSOCKET'
      return self

   def jav_Reset(self):
      self.write("*RST;*CLS;*WAI")

   def jav_logscpi(self):
      self.f = rssd.FileIO.FileIO()       #pylint:disable=E1101
      self.Ofile = "yaVISA"
      DataFile = self.f.Init("yaVISA")    #pylint:disable=W0612

   def jav_read_raw(self):
      # return self.K2.read()
      print('jav_read_raw socket not supported')
      return 9999

   def jav_reslist(self):
      print('Socket does not support Resource list')
      return ["No VISA"]

   def jav_scpilist(self,SCPIList):
      ### Send SCPI list & Query if "?" 
      ### Collect read results into a list for return.
      OutList = []
      for cmd in SCPIList:
         if cmd.find('?') == -1:
            self.write(cmd)
         else:
            ReadStr = self.query(cmd)
            OutList.append(ReadStr)
      return OutList

   def jav_write_raw(self,SCPI):
      self.K2.write(SCPI)                 #pylint:disable=E1101

   def query(self,cmd):
      read ="<notRead>"
      try:
         if self.dataIDN != "":
            cmd = cmd + '\n' 
            self.K2.sendall(cmd.encode()) #Write if connected
            sOut = self.K2.recv(2048).strip()   #read socket
            read = sOut.decode()
      except:
         if self.prnty: print("jav_RdErr : %s-->%s"%(self.Model,cmd))
      if self.Ofile != "" : self.f.write("%s,%s,%s,"%(self.Model,cmd,read))
      return read
      
   def queryFloat(self,cmd):
      try:
         strArry = self.query(cmd).split(',')
         return [float(i) for i in strArry][0]
      except:
         return -9999.9999

   def queryFloatArry(self,cmd):
      try:
         strArry = self.query(cmd).split(',')
         return [float(i) for i in strArry]
      except:
         return [-9999.9999]
         
   def queryInt(self,cmd):
      try:
         strArry = self.query(cmd).split(',')
         return [int(i) for i in strArry][0]
      except:
         return -9999

   def queryIntArry(self,cmd):
      try:
         strArry = self.query(cmd).split(',')
         return [int(i) for i in strArry]
      except:
         return [-9999]

   def write(self,cmd):
      try:
         out = cmd + "\n"
         if self.dataIDN != "": self.K2.sendall(out.encode()) #Write if connected
      except:
         if self.prnty: print("jav_WrtErr: %s-->%s"%(self.Model,cmd))
      if self.Ofile != "" : self.f.write("%s,%s"%(self.Model,cmd))      

if __name__ == "__main__":
   RS = jaVisa().jav_Open("192.168.1.109")
   print(RS.query("*IDN?"))
   print(RS.Device)
   print(RS.jav_Close())

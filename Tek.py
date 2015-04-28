import ctypes
from ctypes import *
from pylab import *
import numpy as np
import matplotlib.animation as animation
import time
from matplotlib.widgets import Button
import matplotlib.pyplot as plt

class SpectrumAnalyzer:

	def __init__(self):
		self.rsa300 = ctypes.WinDLL("RSA300API.dll")
		intArray = c_int * 10
		searchIDs = intArray()
		deviceserial = c_wchar_p()
		numFound = c_int()

		ret = self.rsa300.Search(searchIDs, byref(deviceserial), byref(numFound))
		self.connect(ret, searchIDs)
		self.setParameters()
		self.update()

	def connect(self, ret, searchIDs):
		if ret !=0:
			print "Run error: " + str(ret)
		else:
			self.rsa300.Connect(searchIDs[0])

	def setParameters(self, cf=1800e6, rl=-40, trigPos=25.0, iqBW=100e6):
		self.cf = c_double(cf)
		self.rsa300.SetCenterFreq(self.cf)

		self.rl = c_double(rl)
		self.rsa300.SetReferenceLevel(rl)

		self.trigPos = c_double(trigPos)
		self.rsa300.SetTriggerPositionPercent(self.trigPos)

		self.iqBW = c_double(iqBW)
		self.rsa300.SetIQBandwidth(self.iqBW)


	def getIQData(self):
		aLen = 1280
		length = c_int(aLen)

		iqLen = aLen * 2
		floatArray = c_float * iqLen

		self.rsa300.SetIQRecordLength(length)

		ready = c_bool(False)

		ret = self.rsa300.Run()
		if ret != 0:
			print "Run Error:" + str(ret)
		
		ret = self.rsa300.WaitForIQDataReady(10000, byref(ready))
		if ret != 0:
			print "WaitForIQDataReady error: " + str(ret)

		iqData = floatArray()
		startIndex = c_int(0)

		if ready:
			ret = self.rsa300.GetIQData(iqData, startIndex, length)
			if ret != 0:
				print "GetIQData error: " + str(ret)
			iData = range(0,aLen)
			qData = range(0,aLen)
			for i in range(0,aLen):
				iData[i] = iqData[i*2]
				qData[i] = iqData[i*2+1]

		z = [(x + 1j*y) for x,y in zip(iData, qData)]

		cf = c_double(0)
		self.rsa300.GetCenterFreq(byref(self.cf))
		
		spec2 = mlab.specgram(z, NFFT=aLen, Fs=56e6)
		f = [(x + self.cf)/1e6 for x in spec2[1]]

		spec = np.fft.fft(z, aLen)
		r = [x * 1 for x in abs(spec)]
		r = np.fft.fftshift(r)

		return [iData, qData, z, r, f]


	def update(self):
		aLen = 1280
		x = np.linspace(0, aLen, aLen)
		iq = self.getIQData()

		f = iq[4]
		i = iq[0]
		q = iq[1]
		r = iq[3]

		'''

		for a in range(10):
			print str(f[a]) + " = " + str(r[a])
		print " "

		for a in range(-1,-10,-1):
			print str(f[a]) + " = " + str(r[a])
		print " "		
		'''
	def updateFFT(self):
		aLen = 1280
		x = np.linspace(0, aLen, aLen)
		iq = self.getIQData()

		f = iq[4]
		i = iq[0]
		q = iq[1]
		r = iq[3]

		rDiff = np.diff(r, n=2)

		for a in range(-1,-30,-1):
			print str(f[a]) + " = " + str(r[a])
		print " "

		for a in range(-1,-30,-1):
			print str(f[a]) + " = " + str(rDiff[a])
		print " "		





	def switchFreq(self):
		self.setParameters(cf=1844e6, rl=-40, trigPos=25.0, iqBW=10e6)
		#self.update()
		self.updateFFT()
		#self.setParameters(cf=800e6, rl=-40, trigPos=25.0, iqBW=10e6)
		#self.update()
		#self.updateFFT()

	def cellBand(self,cf=1890e6):
		self.setParameters(cf=cf)
		iqDataInBand = self.getIQData()

		finBand = iqDataInBand[4]
		rinBand = iqDataInBand[3]
		rDinBand = np.diff(rinBand, n=2)

		rinBandMax = np.amax(rDinBand)
		finBandMax = finBand[np.argmax(rDinBand)]

		print rinBandMax
		print np.amax(rDinBand)
		print finBandMax



		#valus not in Band


if __name__ == "__main__":
	rsa300 = SpectrumAnalyzer()
	
	#while(True):
	#	rsa300.switchFreq()

	rsa300.cellBand()
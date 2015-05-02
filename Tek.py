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

		if ret !=0:
			print "Run error: " + str(ret)
		else:
			self.rsa300.Connect(searchIDs[0])
		# we need to store:
		# max value
		# the "delta" change of the values
		# the number of peaks
		# and how long there has been a peak
		
		#self.data = [max_value,change_in_max,number_of_peaks,sum_of_peaks,time]
		self.data = [0,0,0,0,0]

	def setParameters(self, cf=80e6, rl=-10, trigPos=25.0, iqBW=40e6):
		self.rsa300.Stop()
		aLen = 1280
		length = c_int(aLen)

		iqLen = aLen * 2
		floatArray = c_float * iqLen

		self.rsa300.SetIQRecordLength(length)
		
		self.cf = c_double(cf)
		self.rsa300.SetCenterFreq(self.cf)		

		self.rl = c_double(rl)
		self.rsa300.SetReferenceLevel(rl)
		cf = c_double(0)
		self.rsa300.GetReferenceLevel(byref(cf))

		self.trigPos = c_double(trigPos)
		self.rsa300.SetTriggerPositionPercent(self.trigPos)

		self.iqBW = c_double(iqBW)
		self.rsa300.SetIQBandwidth(self.iqBW)

		print cf


	def getIQData(self):
		aLen = 1280
		length = c_int(aLen)

		iqLen = aLen * 2
		floatArray = c_float * iqLen

		#self.rsa300.SetIQRecordLength(length)

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


	def cellBand(self, cf=1871e6):
	
		self.setParameters(cf=cf)
		iqDataInBand = self.getIQData()

		finBand = iqDataInBand[4]
		rinBand = iqDataInBand[3]
		rDinBand = np.diff(rinBand, n=2)

		rDinBandMax = np.amax(rDinBand)
		rinBandMax = rinBand[np.argmax(rinBand)]
		finBandMax = finBand[np.argmax(rinBand)]

		print "Max Value = " + str(rinBandMax)
		print "Max derivative Value = " + str(rDinBandMax)
		print "Corresponding Frequency = " + str(finBandMax)
		print "Frequency range is " + str(finBand[0]) + " to " + str(finBand[1279])

		cf = c_double(0)
		print self.rsa300.GetCenterFreq(byref(cf))

		#below is for printing
				
		#plot(finBand,rinBand)
		#show()

		print self.population(finBand, rinBand)
		plot(finBand,rinBand)
		show()
	
		
	def Stop(self):
		print "Goodbye!"
		self.rsa300.Stop()
		self.rsa300.Disconnect()

	def population(self,frequency,amplitude):
		#self.data = [max_value,change,number_of_peaks,sum_of_peaks,time]
		data = self.data
		max_value = data[0]
		change = data[1]
		number_of_peaks = data[2]
		sum_of_peaks = data[3]
		time = data[4]

		peaks = amplitude[amplitude > 0.1]
		if not peaks:
			change_in_max = 0 - max_value
			max_value = 0

			if time > 0:
				time -= 1
			else:
				time = 0

		else:
			change_in_max = np.amax(peaks) - max_value
			max_value = np.amax(peaks)
			number_of_peaks = np.count_nonzero(peaks)
			sum_of_peaks = np.sum(peaks)

		self.data = []


		

		
if __name__ == "__main__":
	
	rsa300 = SpectrumAnalyzer()
	aLen = 1280

	rsa300.cellBand()
	#rsa300.animation()
	
	rsa300.Stop()


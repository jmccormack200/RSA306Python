import ctypes
from ctypes import *
from pylab import *
import numpy as np
import matplotlib.animation as animation
import time
from matplotlib.widgets import Button
import matplotlib.pyplot as plt
import math

class SpectrumAnalyzer:

	def __init__(self):
		self.rsa300 = ctypes.WinDLL("RSA300API.dll")

		intArray = c_int * 10
		searchIDs = intArray()
		deviceserial = c_wchar_p()
		numFound = c_int()

		self.data = [0,0,0,0,0]
		self.populationValue = 5

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


	def setParameters(self, cf=80e6, rl=-10, trigPos=25.0, iqBW=40e6):
		self.rsa300.Stop()
		aLen = 1280
		length = c_int(aLen)

		iqLen = aLen * 2
		floatArray = c_float * iqLen

		self.rsa300.SetIQRecordLength(length)
		
		cf = c_double(cf)
		self.rsa300.SetCenterFreq(cf)		

		rl = c_double(rl)
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
		self.rsa300.GetCenterFreq(byref(cf))
		
		spec2 = mlab.specgram(z, NFFT=aLen, Fs=56e6)
		f = [(x + cf)/1e6 for x in spec2[1]]

		spec = np.fft.fft(z, aLen)
		r = [x * 1 for x in abs(spec)]
		r = np.fft.fftshift(r)

		return [iData, qData, z, r, f]


	def cellBand(self, cf=1871e6):
	
		self.setParameters(cf=cf, rl=-10)
		iqDataInBand = self.getIQData()

		finBand = iqDataInBand[4]
		rinBand = iqDataInBand[3]
		rDinBand = np.diff(rinBand, n=2)

		rDinBandMax = np.amax(rDinBand)
		rinBandMax = rinBand[np.argmax(rinBand)]
		finBandMax = finBand[np.argmax(rinBand)]

		'''
		print "Max Value = " + str(rinBandMax)
		print "Max derivative Value = " + str(rDinBandMax)
		print "Corresponding Frequency = " + str(finBandMax)
		print "Frequency range is " + str(finBand[0]) + " to " + str(finBand[1279])
		'''

		#below is for printing
				
		#plot(finBand,rinBand)
		#show()
		average = 0

		average += self.population(finBand, rinBand)

		#print "Population = " + str(average)

		
		#plot(finBand,rinBand)
		#show()
	
		
	def Stop(self):
		print "Goodbye!"
		self.rsa300.Stop()
		self.rsa300.Disconnect()

	def population(self,frequency,amplitude):
		#self.data = [max_value,change,number_of_peaks,sum_of_peaks,time]
		old_data = self.data
		old_time = old_data[-1]
		minimum_for_peak = 0.037
		population_score = old_data[4]
		peaks = amplitude[amplitude > minimum_for_peak]

		if len(peaks) == 0:
			max_value = 0
			change = 0
			number_of_peaks = 0
			sum_of_peaks = 0

		else:
			change = 0 # fix in next function
			max_value = np.amax(peaks)
			number_of_peaks = np.count_nonzero(peaks)
			sum_of_peaks = np.sum(peaks)
		
		time = old_time + 1

		'''
		print "Max Value = " + str(max_value)
		print "change = " + str(change)
		print "number of peaks = " + str(number_of_peaks)
		print "sum of peaks = " + str(sum_of_peaks)
		print "time = " + str(time)
		'''
		
		new_data = [max_value, change, number_of_peaks, sum_of_peaks, population_score, time]
		population_value = self.findPopulationValue(old_data, new_data)
		return population_value

	def findPopulationValue(self, old_data, new_data):
		#Adjust these values to adjust the maximum score
		fullMax = 0.4
		fullAvg = 0.18
		fullNumPeaks = 20


		#we need to figure out what went up, and what went down
		# and adjust the popluation value accordingly

		#if we have no new cell data, lower score over time

		if (new_data[-1] >= 30):
			oldPopulation = self.populationValue
			#self.populationValue
			print ""
			print "Weight Value = " + str(new_data[4]/new_data[-1])
			print "Population Value = " + str(round(self.populationValue))

			new_data[4] = 0
			new_data[-1] = 0

		#don't go below 0
		if self.populationValue <= 0:
			self.populationValue = 1

		#if we have cell data calculate population score

		#first calculate if average is increasing or decreasing
		if old_data[2] == 0:
			old_divisor = 1
		else:
			old_divisor = old_data[2]

		if new_data[2] == 0:
			new_divisor = 1
		else:
			new_divisor = new_data[2]

		previousAverage = float(old_data[3])/float(old_divisor)
		newAverage = float(new_data[3])/float(new_divisor)
		deltaAverage = newAverage - previousAverage

		#then see if new max or old max is bigger
		deltaMax = new_data[0] - old_data[0]

		#create weight of the values
		weighted = (((float(new_data[0]/fullMax)) * 0.4) + (float(newAverage/fullAvg)*.2) +
				(float(new_divisor/fullNumPeaks) * 0.4)) * 100
		weighted = round(weighted,2)

		#print "weighted = " + str(weighted)
		#store data and print value
		#print weighted
		new_data[4] += weighted

		return weighted

		
if __name__ == "__main__":
	
	rsa300 = SpectrumAnalyzer()
	aLen = 1280

	for a in range(6000):
		rsa300.cellBand()
	#rsa300.animation()
	
	rsa300.Stop()


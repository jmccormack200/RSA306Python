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
		#self.rsa300.SetTriggerMode(mode=1)

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

		#print iq[4][1][0:10]
		line.set_data(x, i)
		line2.set_data(x, q)
		ax2.set_xlim(f[0], f[len(f) - 1])
		line3.set_data(f, r)
		
		ax2.set_xticks( [ round(f[int(8.0/56*len(f))]), round(f[int(18.0/56*len(f))]), f[len(f)/2], round(f[int(38.0/56*len(f))]), round(f[int(48.0/56*len(f))]) ] )
		#ax2.relim()
		return line, line2, line3,
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
		self.setParameters(cf=1844e6, rl=-40, trigPos=25.0, iqBW=56e6)
		#self.update()
		self.updateFFT()
		#self.setParameters(cf=800e6, rl=-40, trigPos=25.0, iqBW=10e6)
		#self.update()
		#self.updateFFT()

	def cellBand(self,cf=700e6):
		self.setParameters(cf=cf)
		iqDataInBand = self.getIQData()

		finBand = iqDataInBand[4]
		rinBand = iqDataInBand[3]
		rDinBand = np.diff(rinBand, n=2)

		rinBand = np.log(abs(rinBand))

		rDinBandMax = np.amax(rDinBand)
		rinBandMax = rinBand[np.argmax(rDinBand)]
		finBandMax = finBand[np.argmax(rDinBand)]
		print np.amax(finBand)

		'''
		rDinBandMax = 0
		rinBandMax = np.amax(rinBand)
		finBandMax = finBand[np.argmax(rinBand)]
		'''



		print "Max Value = " + str(rinBandMax)
		print "Max derivative Value = " + str(rDinBandMax)
		print "Corresponding Frequency = " + str(finBandMax)
		print "Frequency range is " + str(finBand[0]) + " to " + str(finBand[1279])

		cf = c_double(0)
		print self.rsa300.GetCenterFreq(byref(cf))

		plot(finBand,rinBand)
		show()

		#valus not in Band


if __name__ == "__main__":
	rsa300 = SpectrumAnalyzer()
	
	#while(True):
	#	rsa300.switchFreq()

	rsa300.cellBand()


	fig = figure()

	ax2 = fig.add_subplot(211)
	ax2.set_xlim(0, aLen)
	ax2.set_ylim(0, 1e2)
	ax2.set_yscale('symlog')

	xlabel('RefLevel = ' + str(rl.value) + ' dBm')
	title('IQBandwith = ' + str(iqBW.value / 1e6) + ' MHz')
	ax = fig.add_subplot(212)
	ax.set_xlim(0, aLen)
	ax.set_ylim(-15e-3, 15e-3)

	xlabel('CF = ' + str(cf.value / 1e6) + ' MHz')
	line, = ax.plot([], [], lw=2)
	line2, = ax.plot([], [], lw=2)
	line3, = ax2.plot([], [], lw=2)
	ani = animation.FuncAnimation(fig, update, init_func=init, frames=200, interval=10, blit=True)
	show()
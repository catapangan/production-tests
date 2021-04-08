#!/usr/bin/python3

import os
import time

def readBuffer(buffer_loc):
		buffer_pipe = None
		try:
			if os.path.exists(buffer_loc):
				buffer_pipe = os.popen('cat ' + buffer_loc)
				output = buffer_pipe.read()
			else:
				raise Exception('Path:' + buffer_loc + ' does not exist')
		except Exception as e:
			print(str(e))
			if buffer_pipe is not None:
				buffer_pipe.close()
			return False
		buffer_pipe.close()
		return output

def writeBuffer(wstring, buffer_loc):
	buffer_pipe = None
	try:
		if os.path.exists(buffer_loc):
				buffer_pipe = os.popen("echo " + str(wstring) + " > " + buffer_loc)
		else:
			raise Exception('Path:' + buffer_loc + ' does not exist')
	except Exception as e:
		print(str(e))
		if buffer_pipe is not None:
			buffer_pipe.close()
		return False
	buffer_pipe.close()
	return True

class AD7124():
	def __init__(self):
		self.dev_name = "ad7124"
		self.dev_buffer = 0

		self.vref = 2.5
		self.__raw_max = 2**24 - 1
		self.__raw_min = 0

		self.channels = [
			'in_voltage0-voltage1',
			'in_voltage2-voltage3',
			'in_voltage4-voltage5',
			'in_voltage6-voltage7',
			'in_voltage8-voltage9',
			'in_voltage10-voltage11',
			'in_voltage12-voltage13',
			'in_voltage14-voltage15'
		]

		self.data = {}
		for ch in self.channels:
			self.data[ch] = {
				'raw': 0,
				'offset': 0,
				'scale': 0,
				'ext_gain': 10
			}

	def getVoltage(self, ch):
		if self.dev_buffer == 0:
			return 0

		try:
			tmp_val = readBuffer(self.dev_buffer + '/' + ch + '_raw')

			if tmp_val == False:
				print('Channel: ' + ch + ' does not exist')
				return False
			
			tmp_val = int(tmp_val)
			if tmp_val > self.__raw_max or tmp_val < self.__raw_min:
				print('Raw data is out of bounds')
				return False

			self.data[ch]['raw'] = tmp_val
		except Exception as e:
			print(str(e))
		
		return self.data[ch]['raw'] * self.data[ch]['scale'] * self.data[ch]['ext_gain']

	def loadChannelSettings(self):
		if self.dev_buffer == 0:
			return False

		numError = 0
		for ch in self.data:
			tmp_val_1 = readBuffer(self.dev_buffer + '/' + ch + '_scale')
			tmp_val_2 = readBuffer(self.dev_buffer + '/' + ch + '_offset')

			if tmp_val_1 == False or tmp_val_2 == False:
				numError += 1
				print('Channel: ' + ch + ' does not exist')
			else:
				self.data[ch]['scale'] = float(tmp_val_1)
				self.data[ch]['offset'] = float(tmp_val_2)
				
		if numError == 0:
			return True
		return False

class LT2688():
	def __init__(self):
		self.dev_name = "ltc2688"
		self.dev_buffer = 0

		self.vref = 4.096
		self.__raw_max = (2**16) - 1
		self.__raw_min = 0

		self.channels = [
			'out_voltage0',
			'out_voltage1',
			'out_voltage2',
			'out_voltage3',
			'out_voltage4',
			'out_voltage5',
			'out_voltage6',
			'out_voltage7',
			'out_voltage8',
			'out_voltage9',
			'out_voltage10',
			'out_voltage11',
			'out_voltage12',
			'out_voltage13',
			'out_voltage14',
			'out_voltage15'
		]

		self.data = {}
		for ch in self.channels:
			self.data[ch] = {
				'raw': 0,
				'scale': 2.4414 * self.vref / self.__raw_max
			}

	def getVoltage(self, ch):
		if self.dev_buffer == 0:
			return 0

		tmp_val = readBuffer(self.dev_buffer + '/' + ch + '_raw')

		if tmp_val == False:
			print('Channel: ' + ch + ' does not exist')
			return False

		if tmp_val > self.__raw_max or temp < self.__raw_min:
			print('Raw data is out of bounds')
			return False

		self.data[ch]['raw'] = int(tmp_val)
		return self.data[ch]['raw'] * self.data[ch]['scale']

	def setVoltage(self, ch, voltage):
		if self.dev_buffer == 0:
			return False
		
		ch_vmax = self.__raw_max * self.data[ch]['scale']
		ch_vmin = self.__raw_min * self.data[ch]['scale']

		if voltage > ch_vmax:
			voltage = ch_vmax

		if voltage < ch_vmin:
			voltage = ch_vmin

		self.data[ch]['raw'] = int(voltage/self.data[ch]['scale'])
		tmp_val = writeBuffer(self.data[ch]['raw'], self.dev_buffer + '/' + ch + '_raw')

		if tmp_val == False:
			print('Channel: ' + ch + ' does not exist')
			return False
		
		return voltage

	def loadChannelSettings(self):
		if self.dev_buffer == 0:
			return False

		numError = 0
		for ch in self.data:
			tmp_val = readBuffer(self.dev_buffer + '/' + ch + '_scale')

			if tmp_val == False:
				numError += 1
				print('Channel: ' + ch + ' does not exist')
			else:
				self.data[ch]['scale'] = float(tmp_val)
				
		if numError == 0:
			return True
		return False
		
class CN0554():

	def __init__(self):
		self.adc = AD7124()
		self.dac = LT2688()

		self.loopbackPairs = [
			[('out_voltage0', 'out_voltage1'), 'in_voltage0-voltage1'],
			[('out_voltage2', 'out_voltage3'), 'in_voltage2-voltage3'],
			[('out_voltage4', 'out_voltage5'), 'in_voltage4-voltage5'],
			[('out_voltage6', 'out_voltage7'), 'in_voltage6-voltage7'],
			[('out_voltage8', 'out_voltage9'), 'in_voltage8-voltage9'],
			[('out_voltage10', 'out_voltage11'), 'in_voltage10-voltage11'],
			[('out_voltage12', 'out_voltage13'), 'in_voltage12-voltage13'],
			[('out_voltage14', 'out_voltage15'), 'in_voltage14-voltage15']
		]

		if self.getBuffers() == False:
			if self.adc.dev_buffer == 0:
				print("No ADC device!")
			if self.dac.dev_buffer == 0:
				print("No DAC device!")

		self.adc.loadChannelSettings()
		#self.dac.loadChannelSettings()

	def getBuffers(self):
		try:
			if os.path.isdir('/sys/bus/iio/devices'):
				dev_num = 0
				while True:
					buffer = '/sys/bus/iio/devices/iio:device' + str(dev_num)
					if os.path.exists(buffer):
						if self.adc.dev_buffer == 0 and self.getDeviceName(buffer).startswith(self.adc.dev_name):
							self.adc.dev_buffer = buffer
						if self.dac.dev_buffer == 0 and self.getDeviceName(buffer).startswith(self.dac.dev_name):
							self.dac.dev_buffer = buffer
					else:
						break

					if self.adc.dev_buffer != 0 and self.dac.dev_buffer != 0:
						break

					dev_num += 1

				if self.adc.dev_buffer != 0 and self.dac.dev_buffer != 0:
					return True
							
			else:
				raise Exception("IIO devices are unavailable")
	
		except Exception as e:
			print(str(e))

		return False

	def getDeviceName(self, dev_buffer):
		name_loc = dev_buffer + str('/name')

		try:
			if os.path.exists(name_loc):
				dev_pipe = os.popen('cat ' + name_loc)
				dev_name = dev_pipe.read()
			else:
				raise Exception("IIO device has no name info")

		except Exception as e:
			print(str(e))
			dev_name = 0

		return dev_name

	def productionTest(self):
		result_DAC = {}
		result_ADC = {}

		for pair in self.loopbackPairs:
			result_DAC[pair[0][0]] = self.dac.setVoltage(pair[0][0], 10)
			result_DAC[pair[0][1]] = self.dac.setVoltage(pair[0][1], 0)
		
			result_ADC[pair[1]] = self.adc.getVoltage(pair[1])

			print("DAC:" + str(result_DAC[pair[0][0]] - result_DAC[pair[0][1]]))
			print("ADC RAW:" + str(self.adc.data[pair[1]]['raw']) + ", SCALE:" + str(self.adc.data[pair[1]]['scale']) + ", FLOAT:" + str(result_ADC[pair[1]]))

def main():
	dev = CN0554()
	dev.productionTest()

if __name__ == '__main__':
	main()
#!/usr/bin/env python3
#-*- coding:utf-8 -*-

# univariate lstm example
import time,datetime
from time import process_time
import json
import os, psutil
from math import *

from os import listdir
from os.path import isfile, join
from opcua import Client 

import tensorflow as tf
import numpy as np
from numpy import array
from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.layers import LSTM, CuDNNGRU, CuDNNLSTM, Activation, Dropout
from tensorflow.python.keras.layers import Dense

tf.config.run_functions_eagerly(False)  ## momory reak

i=0
j=0
k=0

error_Pred = 0.0
comp_predictVal = 0.0

url = "opc.tcp://192.168.0.15:48400"     ##pi opccpuserver 

client= Client(url) 
client.connect() 
print("OPCUA SERVER Connected") 
print("server start at ".format(url))

aqInterval = 1       ## data sampleing interval
No_datasize = 180      ## data size

data = list()
listdata = list()
realdataList = list()
listpredictdata = list()

InitPredict_Val = 0.0

waitsec = 20.0   # <--- Prediction interval allow range
waitsec_Over = 30.0
waitsec_Etc = 60.0

epoch_Size = 20
batchSize = 9

## Call lastest json file
filepath = '/home/royal/jsondata/'
files = [f for f in listdir(filepath) if isfile(join(filepath, f))]
No = len(files)
lastfile = No - 1
jsonfileName = filepath + files[No-1]


## Call last predict data file in folder
pred_Filepath = '/home/royal/predictdata/'
predFiles = [f for f in listdir(pred_Filepath) if isfile(join(pred_Filepath, f))]
pNo = len(predFiles)
Plastfile = pNo -  1
predictfileName = pred_Filepath + predFiles[pNo-1]


################################################# OPCUA FUNCTION
#async def opcuaFunction():

def opcuaFunction():
## Reopen OLD json data file
        print()

        opcStart = process_time()

        with open(jsonfileName, "r") as read_json:
             listdata = json.load(read_json)

## Initialize data : first data size 180 create json data array
        if len(listdata) < No_datasize:
               print("please create Data number 180 file")
## Start roop data aquire
        else:
               del listdata[0]         ## First data delete for newdata
               Val10 = client.get_node("ns=2;i=3")   ## opc client restsrt
               fVal10 = round(Val10.get_value(),2)  ## 0.00 express
               listdata.append(abs(fVal10))
               with open(jsonfileName, "w") as ff:
                    json.dump(listdata, ff)
               print("[OPCUA] Lastest OPCUA Input value is [%.1f]" %fVal10)

               ## read previous predict data && compare recent input data
               with open(predictfileName, "r") as old_rf:
                    listpredictdata = json.load(old_rf)

               size_oldpredict_List = len(listpredictdata)
               print(">>> Old predict data size : ", size_oldpredict_List)

               comp_predictValue = listpredictdata[size_oldpredict_List-1]   ## not now execute cudnn predict new value
               error_Pred = abs(comp_predictValue-fVal10)
               print(">>> Compare >>> Old predict value: [%.1f], New input value: [%.1f], Error: [%.1f]"%(comp_predictValue,fVal10,error_Pred))
               print()


        opcEnd = process_time()
        opcTime =  opcEnd - opcStart
        print("[OPCUA] OPCUA time elapse : %.3f sec" %opcTime)
        return opcTime
################################################# OPCUA FUNCTION END


################################################# CUDNN FUNCTION
# split a univariate sequence into samples

def split_sequence(sequence, n_steps):
        X, y = list(), list()
        for i in range(len(sequence)):
                # find the end of this pattern
                end_ix = i + n_steps
                # check if we are beyond the sequence
                if end_ix > len(sequence)-1:
                        break
                # gather input and output parts of the pattern
                seq_x, seq_y = sequence[i:end_ix], sequence[end_ix]
                X.append(seq_x)
                y.append(seq_y)
        return array(X), array(y)

def cudnnFunction():
#open json data file
        tf.keras.backend.clear_session()

        start_Time = process_time()

        print("[CUDNN]>>>CUDNN epoch size : %d , batch_size : %d"%(epoch_Size, batchSize))

        with open(jsonfileName, "r") as read_json:
             listdata = json.load(read_json)

        with open(predictfileName, "r") as pre_f:
             listpredictdata = json.load(pre_f)

        del listpredictdata[0]

        raw_seq =  listdata
        calSize = len(raw_seq)
        print()
        #print("[CUDNN]>>> Number of calculation  size is ",len(raw_seq))

# choose a number of time steps
        n_steps = 3
# split into samples
        X, y = split_sequence(raw_seq, n_steps)
# reshape from [samples, timesteps] into [samples, timesteps, features]
        n_features = 1
        X = X.reshape((X.shape[0], X.shape[1], n_features))
# initialize keras model for loop interval
# define model
        model = Sequential()

#CuDNNGRU model
        model.add(CuDNNGRU(180, input_shape = (n_steps, n_features), return_sequences = True))
        #model.add(Dropout(0.2))
        model.add(CuDNNGRU(180))
        #model.add(Dropout(0.2))
        model.add(Activation('tanh'))
        model.add(Dense(1))
        model.compile(optimizer='adam', loss='mse')

# fit model
        model.fit(X, y, epochs=epoch_Size, batch_size=batchSize, verbose=0, validation_split=0.0)
        model.reset_states()

# demonstrate prediction
        x_input = array([raw_seq[calSize-3], raw_seq[calSize-2], raw_seq[calSize-1]])
        x_input = x_input.reshape((1, n_steps, n_features))
        yhat = model.predict(x_input, verbose=0)
        print()
        print("====================================> CUDNN Predict Value : [ %.1f ]" %yhat)
        print()

        Dim1 = yhat.reshape(-1,)
        yhatlist = Dim1.tolist()

        yhatlist_Size = len(yhatlist)
        temp_Val = yhatlist[yhatlist_Size-1]

        listpredictdata.append(round(temp_Val,2))

        with open(predictfileName, "w") as x:
             json.dump(listpredictdata, x)

# Wait for completion
        end_Time = process_time()
        elapsedTime = end_Time - start_Time
        print("[CUDNN]>>>CUDNN running total time duration: %.3f sec" %elapsedTime)

        return elapsedTime

#################################################### CUDNN FUNCTION END


##---------------------------------------------------MAIN FUNCTION START ->
if __name__ == '__main__':
# No async function need
	try:
		time.sleep(1)
		while True:

			if k < 180:
				print("................................................................................  OK Loop continue") 
			else:
				k = 0
				print("--------------------------------------------------------------------------------  END LOOP")
				break

			print()
			print()
			start = process_time()
			print(f'................................................................................  Loop number ( {k} )')
			opcT = opcuaFunction()  ## first data aquire
			cudnnT = cudnnFunction()  ## end run cudnn pedict function

			if cudnnT <=18.0:
				waitT = waitsec
				print("... Interval time set: [%.1f] "%waitT)
			elif 18.0<cudnnT<=30.0:
				waitT = waitsec_Over
				print("[Warning] Each loop time should be under 20 sec depending on CUDNN ... Interval time set : [%.1f]"%waitT) 
			elif 30.0<cudnnT<=60.0:
				waitT = waitsec_Etc
				print("[Warning] Each loop time should be under 20 sec depending on CUDNN ... Interval time set : [%.1f]"%waitT) 
			else:
				print("[ERROR]Time over CUDNN calculation error -  please retreat the cudnnFunction() parameter")
				break
			total_Elapse = opcT+cudnnT
			tt = waitT - total_Elapse
			time.sleep(tt)

			end = process_time()
			print()
			print(f'>>> Time elapse sec : OPCUA={round(opcT,4)}, CUDNN={round(cudnnT,4)}')
			print('>>> Total Main loop interval Lapse time: %.3f sec'%(end-start))

			k+=1

	except KeyboardInterrupt:
    		print('Ctrl + C STOP running')

	client.disconnect()
	print()
	print("OPCUA Server disconnected  at ".format(url))
	print("Please check OPCUA json data file: ", format(jsonfileName))
	print("Please check CUDNN PREDICT data file: ", format(predictfileName))
	print("CuDNN Model  CuDNNGRU") 
##-------------------------------------------------------------------------

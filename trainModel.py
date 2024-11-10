'''
Created on 18 oct. 2024

@author: christophe
'''

if __name__ == '__main__':
    pass

# TensorFlow and tf.keras
import tensorflow as tf
from tensorflow import keras


# Helper libraries
import numpy as np
import matplotlib.pyplot as plt





''' import dataset '''

features= np.load('data/observations.npy')
labels = np.load('data/labels.npy')
ids = np.load('data/ids.npy')

labelList = [] 


trainTestLimit = 3000

train_features = features [trainTestLimit:]
train_labels = labels [trainTestLimit:]

test_features = features [0:trainTestLimit]
test_labels = labels [0:trainTestLimit]
testData = (test_features, test_labels)



''' build model '''         

model = keras.Sequential()


model.add(keras.layers.Flatten(input_shape=(11, 5, 22, 17))) # (context, chromatic and enharmonic pitches, other params)
model.add(keras.layers.Dense(10)) 
model.add(keras.layers.Dense(3, activation=tf.nn.softmax)) # label values       
        


''' compile model '''
model.compile(optimizer="adam",  loss='sparse_categorical_crossentropy',metrics=['accuracy'])

#''' callbacks '''
cb = keras.callbacks.TensorBoard(log_dir='/Users/Christophe/Desktop/dataset/logs', 
                                 histogram_freq=0, batch_size=200, write_graph=True, 
                                 write_grads=False, write_images=False, embeddings_freq=0, 
                                 embeddings_layer_names=None, 
                                 embeddings_metadata=None, embeddings_data=None)


''' train model '''
#history = model.fit(train_features, train_labels, epochs=12)

history = model.fit(train_features, train_labels, epochs=200, batch_size=3000, validation_data=testData, callbacks=[cb])
history_dict = history.history



''' evaluate accuracy'''
test_loss, test_acc = model.evaluate(test_features, test_labels)
print('Test accuracy:', test_acc)


''' save model '''

model.save('model/cadenceModel.h5')


#===============================================================================
# new_model = keras.models.load_model('/Users/Christophe/Desktop/dataset/model.h5')
# new_model.compile(optimizer=tf.train.AdamOptimizer(),  loss='sparse_categorical_crossentropy',metrics=['accuracy'])
# new_model.summary()
# 
# loss, acc = new_model.evaluate(test_features, test_labels)
# print("Restored model, accuracy: {:5.2f}%".format(100*acc))
#===============================================================================


''' graph'''
acc = history.history['accuracy']
val_acc = history.history['val_accuracy']
loss = history.history['loss']
val_loss = history.history['val_loss']
 
epochs = range(1, len(acc) + 1)
 
# "bo" is for "blue dot"
acc_values = history_dict['accuracy']
val_acc_values = history_dict['val_accuracy']
 
plt.plot(epochs, acc, 'bo', label='Training acc')
plt.plot(epochs, val_acc, 'b', label='Validation acc')
plt.title('Training and validation accuracy')
#plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
 
 
#===============================================================================
# plt.plot(epochs, loss, 'bo', label='Training loss')
# plt.plot(epochs, val_loss, 'b', label='Validation loss')
# plt.title('Training and validation loss')
# #plt.xlabel('Epochs')
# plt.ylabel('Loss')
# plt.legend()
#===============================================================================
 
plt.show()




#''' a few predictions '''
#===============================================================================
predictions = model.predict(features)
# 
#  
print ("prediction: " + str(predictions[0]) + "truth: " + str(labels[0]))
print ("prediction: " + str(predictions[16]) + "truth: " + str(labels[16]))
# 
# 
# predictions = new_model.predict(features)
# 
# print ("prediction: " + str(predictions[0]) + "truth: " + str(labels[0]))
# print ("prediction: " + str(predictions[1]) + "truth: " + str(labels[1]))
#===============================================================================





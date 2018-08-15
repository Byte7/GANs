from __future__ import print_function, division

from keras.datasets import mnist
from keras.layers import Input, Dense, Reshape, Flatten, Dropout
from keras.layers import BatchNormalization, Activation, ZeroPadding2D
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.convolutional import UpSampling2D, Conv2D
from keras.models import Sequential, Model
from keras.optimizers import Adam

import matplotlib.pyplot as plt
plt.switch_backend('agg')
import numpy as np


class DCGAN():

    def __init__(self):
        self.img_rows = 28
        self.img_cols = 28
        self.channels = 1
        self.img_shape = (self.img_rows, self.img_cols, self.channels)
        self.dimen = 100

        optimizer = Adam(0.0002, 0.5)

        self.discriminator = self.build_discriminator()
        self.discriminator.compile(loss='binary_crossentropy', optimizer=optimizer, metrics=['accuracy'])

        self.generator = self.build_generator()
        self.generator.compile(loss='binary_crossentropy', optimizer=optimizer, metrics=['accuracy'])

        # The generator takes noise as input and generates imgs
        noi = Input(shape=(self.dimen,))
        img = self.generator(noi)

        # For the combined model we will only train the generator
        self.discriminator.trainable = False

        # The discriminator takes generated images as input and determines validity
        validity = self.discriminator(img)

        # The combined model  (stacked generator and discriminator)
        # Trains the generator to fool the discriminator
        self.combined = Model(noi, validity)
        self.combined.compile(loss='binary_crossentropy', optimizer=optimizer)

    def build_generator(self):

        model = Sequential()
        model.add(Dense(128*7*7, activation='relu', input_dim=self.dimen))
        model.add(Reshape((7, 7, 128)))
        model.add(UpSampling2D())
        model.add(Conv2D(128, kernel_size=3, padding='same'))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Activation('relu'))
        model.add(UpSampling2D())
        model.add(Conv2D(64, kernel_size=3, padding='same'))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Activation('relu'))
        model.add(Conv2D(self.channels, kernel_size=3, padding='same'))
        model.add((Activation('tanh')))

        model.summary()

        noise = Input(shape=(self.dimen,))
        img = model(noise)
        return Model(noise, img)

    def build_discriminator(self):

        model = Sequential()
        model.add(Conv2D(32, kernel_size=3, strides=2, input_shape=self.img_shape, padding="same"))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dropout(0.3))
        model.add(Conv2D(64, kernel_size=3, strides=2, padding='same'))
        model.add(ZeroPadding2D(padding=((0, 1), (0, 1))))
        model.add(BatchNormalization(momentum=0.8))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dropout(0.3))
        model.add(Conv2D(128, kernel_size=3, strides=2, padding='same'))
        model.add(BatchNormalization(momentum=0.8))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dropout(0.3))
        model.add(Conv2D(256, kernel_size=3, strides=1, padding='same'))
        model.add(BatchNormalization(momentum=0.8))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dropout(0.3))
        model.add(Flatten())
        model.add(Dense(1, activation='sigmoid'))

        model.summary()

        img = Input(shape=self.img_shape)
        valid = model(img)

        return Model(img, valid)

    def train(self, epochs, batch_size=128, sample_size=50):

        # load mnist data
        (X_train, _), (_, _) = mnist.load_data()

        # Rescale -1 to 1
        X_train = X_train / 127.5 - 1.
        X_train = np.expand_dims(X_train, axis=3)

        # adversial ground truth
        valid = np.ones((batch_size, 1))
        fake = np.zeros((batch_size, 1))
        for epoch in range(epochs):

            # Training discriminator
            ids = np.random.randint(0, X_train.shape[0], batch_size)
            imgs = X_train[ids]

            noise = np.random.normal(0, 1, (batch_size, self.dimen))

            # Generate new images
            generate_img = self.generator.predict(noise)

            # train
            dis_loss_real = self.discriminator.train_on_batch(imgs, valid)
            dis_loss_fake = self.discriminator.train_on_batch(generate_img, fake)

            dis_loss = np.add(dis_loss_real, dis_loss_fake)

            # Training generator
            noise = np.random.normal(0, 1, (batch_size, self.dimen))

            # train generator
            gen_loss = self.combined.train_on_batch(noise, valid)

            print("%d [D loss: %f, acc.: %.2f%%] [G loss: %f]" % (epoch, dis_loss[0], 100 * dis_loss[1], gen_loss))

            if epoch % sample_size == 0:
                self.sample_image(epoch)

    def sample_image(self, epoch):
        ri, ci = 5, 5
        noise = np.random.normal(0, 1, (ri * ci, self.dimen))
        g_imgs = self.generator.predict(noise)

        g_imgs = 0.5 * g_imgs + 0.5
        fig, axs = plt.subplots(ri, ci)
        cnt = 0
        for i in range(ri):
            for j in range(ci):
                axs[i, j].imshow(g_imgs[cnt, :, :, 0], cmap='gray')
                axs[i, j].axis('off')
                cnt += 1
        fig.savefig("images/%d.png" % epoch)

        plt.close()


if __name__ == "__main__":
    dcgan = DCGAN()
    dcgan.train(epochs=5000, batch_size=32, sample_size=100)

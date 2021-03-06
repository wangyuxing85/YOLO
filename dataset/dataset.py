'''
Author:
	Charles
Function:
	load data for training
'''
import os
import sys
import random
from torch.utils.data import Dataset
sys.path.append('..')
from utils.utils import *


'''
Function:
	dataset, provide data for training.
Input:
	-root: imgs folder.
	-shape: imgs shape.
	-shuffle: whether shuffle the data or not.
	-transform/target_transform: for data augmentation.
	-is_train: for train or test.
	-seen: the number of pictures fed into network.
	-num_workers: the number of workers.
	-is_multiscale: whether change the size of input images or not.
	-batch_size: the data size of a batch.
'''
class myDataset(Dataset):
	def __init__(self, root, shape=None, **kwargs):
		shuffle = kwargs.get('shuffle')
		with open(root[0], 'r') as file:
			self.imgpaths = file.readlines()
		if root[1] is not None:
			with open(root[1], 'r') as file:
				self.labpaths = file.readlines()
			assert len(self.imgpaths) == len(self.labpaths)
		if shuffle:
			random.shuffle(self.imgpaths)
		self.root = root
		self.nSamples  = len(self.imgpaths)
		self.transform = kwargs.get('transform')
		self.target_transform = kwargs.get('target_transform')
		self.is_train = kwargs.get('is_train')
		self.shape = shape
		self.seen = kwargs.get('seen') if kwargs.get('seen') else 1
		self.num_workers = kwargs.get('num_workers') if kwargs.get('num_workers') else 1
		self.is_multiscale = kwargs.get('is_multiscale')
		self.jitter = kwargs.get('jitter')
		self.hue = kwargs.get('hue')
		self.saturation = kwargs.get('saturation')
		self.exposure = kwargs.get('exposure')
		self.max_object = kwargs.get('max_object')
		self.batch_size = kwargs.get('batch_size')
	def __len__(self):
		return self.nSamples
	def __getitem__(self, index):
		assert index <= len(self)
		imgpath = self.imgpaths[index].rstrip()
		if self.root[1] is None:
			labpath = imgpath.replace('images', 'labels').replace('JPEGImages', 'labels').replace('.jpg', '.txt').replace('.png', '.txt')
		else:
			labpath = self.labpaths[index].rstrip()
		if self.is_multiscale:
			if self.is_train and index % self.batch_size == 0:
				if self.seen < 4000*self.batch_size:
					width = 13 * 32
					self.shape = (width, width)
				elif self.seen < 8000*self.batch_size:
					width = (random.randint(0, 3) + 13) * 32
					self.shape = (width, width)
				elif self.seen < 12000*self.batch_size:
					width = (random.randint(0, 5) + 12) * 32
					self.shape = (width, width)
				elif self.seen < 16000*self.batch_size:
					width = (random.randint(0, 7) + 11) * 32
					self.shape = (width, width)
				else:
					width = (random.randint(0, 9) + 10) * 32
					self.shape = (width, width)
		if self.is_train:
			img, label = load_detection_daug(imgpath, labpath, self.shape, self.jitter, self.hue, self.saturation, self.exposure, max_object=self.max_object)
		else:
			img = Image.open(imgpath).convert('RGB')
			if self.shape:
				img = img.resize(self.shape)
			label = torch.zeros(self.max_object*5)
			try:
				tmp = torch.from_numpy(read_truths(labpath, min_box_scale=8.0/img.width, is_changed=True).astype('float32'))
			except Exception:
				print('[Warning]:%s has no data...' % labpath)
				tmp = torch.zeros(1, 5)
			tmp = tmp.view(-1)
			tmp_size = tmp.numel()
			if tmp_size > self.max_object * 5:
				label = tmp[0: self.max_object*5]
			elif tmp_size > 0:
				label[0: tmp_size] = tmp
		if self.transform is not None:
			img = self.transform(img)
		if self.target_transform is not None:
			label = self.target_transform(label)
		if self.num_workers > 0:
			self.seen = self.seen + self.num_workers
		elif self.num_workers == 0:
			self.seen += 1
		else:
			print('[Error]:num_workers must greater than zero...')
			sys.exit(0)
		return (img, label)
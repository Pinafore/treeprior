from 	math 				import log
from	nltk.tokenize		import TreebankWordTokenizer
from 	collections 		import defaultdict, Counter
from 	random 				import random, randint
from 	glob 				import glob
from 	nltk.corpus 		import stopwords
from 	nltk.corpus			import wordnet as wn
from 	nltk.probability	import FreqDist
from	common				import *
from	operator			import itemgetter


import	re
import 	argparse
import 	time
import	string
import	pickle
import	os.path
import	shutil
import	sys

string.punctuation += '°！”＃€％&／（）＝？｀±´＊——：；》@…～≤÷≈‚。，－’＊^_•｜＜＞，．／¢∞§¶•【】=」￥“'

TAG_EN			= 'en'
TAG_ZH			= 'cmn'
TAG_TR			= 'tr'
TAG_UZ			= 'uz'
TAG_HA			= 'ha'
UNASSIGNED 		= -1
DOCUMENT		= -1
TOPIC			= -2
kTOKENIZER		= TreebankWordTokenizer()
CACHE_DIR		= './cache'
EMPTYWORD		= ''
MIN_LENGTH		= 3
MIN_LENGTH_CMN	= 2

threshold		= defaultdict(float)
threshold[TAG_EN] = 0.2
threshold[TAG_ZH] = 0.25
threshold[TAG_TR] = 0.3


def dict_sample(d, cutoff=-1):
	"""
	Sample a key from a dictionary using the values as probabilities (unnormalized)
	"""
	if cutoff==-1: cutoff = random()
	normalizer = float(sum(d.values()))

	current = 0
	for i in d:
		assert(d[i] > 0)
		current += float(d[i]) / normalizer
		if current >= cutoff: return i
	print("Didn't choose anything: ", cutoff, current)


def lgammln(xx):
	"""
	Returns the gamma function of xx.
	Gamma(z) = Integral(0,infinity) of t^(z-1)exp(-t) dt.
	Usage: lgammln(xx)
	Copied from stats.py by strang@nmr.mgh.harvard.edu
	"""

	assert xx > 0, "Arg to gamma function must be > 0; got %f" % xx
	coeff = [76.18009173, -86.50532033, 24.01409822, -1.231739516,
			 0.120858003e-2, -0.536382e-5]
	x = xx - 1.0
	tmp = x + 5.5
	tmp = tmp - (x + 0.5) * log(tmp)
	ser = 1.0
	for j in range(len(coeff)):
		x = x + 1
		ser = ser + coeff[j] / x
	return -tmp + log(2.50662827465 * ser)


def tokenize_file(filename):
	contents = open(filename).read()
	for ii in kTOKENIZER.tokenize(contents): yield ii



class RandomWrapper:
	"""
	Class to wrap a random number generator to facilitate deterministic testing.
	"""

	def __init__(self, buff):
		self._buffer = buff
		self._buffer.reverse()

	def __call__(self):
		val = self._buffer.pop()
		print("Using random value %0.2f" % val)
		return val




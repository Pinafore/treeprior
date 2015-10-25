from common import *


"""""""""""""""""""""""""""""""""""
CorpusLoader
"""""""""""""""""""""""""""""""""""

class CorpusLoader:

	def __init__(self, corpus_dir, stop='', limit=50, language_list=[TAG_EN,TAG_TR,TAG_ZH]):


		self._language_list		=	language_list
		self._num_tokens		=	defaultdict(int)
		self._doc_tokens		=	defaultdict(list)
		self._doc_strings		=	defaultdict(list)
		self._doc_word_id		=	defaultdict(list)
		self._corpus_dir		=	corpus_dir
		self._limit				=	limit
		self._stopwords			=	[]
		self._stopwords_dir		=	stop
		self._num_docs			=	0.0

		self._tf_normalizer		=	0
		self._doc_freq			=	FreqDist()
		self._term_freq			=	Counter()

		self._vocablist 		=	[]

		if stop is not '':

			for lang_id in self._language_list:
				filename = stop + 'stopword-'+lang_id+'.txt'
				handle = open(filename, 'r')
				for line in handle: self._stopwords.append(line.strip()+'#'+lang_id)
				handle.close()

			print('Using loaded stopword list: ', self._stopwords[:10])


	def scan_corpus(self):

		# we have such procedures:
		#  - load in documents in form of string
		#  - determine the stopword list
		#  - transform documents to token index form
		#  - dump the pickle file

		for lang_id in self._language_list:

			search_path = self._corpus_dir + '/' + lang_id + '/*.txt'
			files = glob(search_path)
			self._tf_normalizer = 0
			print('Loading in language corpus of ', lang_id)


			if len(files) > 0:

				count 				=	0
				self._tf_normalizer	=	0
				self._doc_freq		=	FreqDist()
				self._term_freq		=	Counter()

				if self._limit == -1:
					for ii in files:
						self.scan_doc(tokenize_file(ii), lang_id)
						count += 1
					self._num_docs = count
				else:
					self._num_docs = self._limit
					for ii in files:
						count += 1
						if count > self._limit: break
						self.scan_doc(tokenize_file(ii), lang_id)


				if (self._stopwords_dir is ''):
					self.determine_stopwords(count-1, lang_id)

			else:
				print('Skip language ' + lang_id + '. There\'s no file in this language.')


		self._vocablist = set(self._vocablist)


	def scan_doc(self, doc, lang_id):

		doc_id		=	len(self._doc_strings)
		new_doc		=	[]

		for token in doc:

			token = ''.join(x for x in token if not x.isdigit() and x not in string.punctuation)
			if (token == ''): continue
			token = token.lower() + '#' + lang_id

			if lang_id == TAG_ZH:
				if (len(token[:-4]) >= MIN_LENGTH_CMN):
					self._term_freq[token] += 1
					new_doc.append(token)
			elif (len(token[:-3]) >= MIN_LENGTH):
				self._term_freq[token] += 1
				new_doc.append(token)

		for token in set(new_doc): self._doc_freq[token] += 1

		self._doc_strings[doc_id] = new_doc
		self._tf_normalizer += len(new_doc)


	def determine_stopwords(self, corpus_size, lang_id):

		handle = open('stopword-'+lang_id+'.txt', 'w')
		print('Printing out stopword list of language: ', lang_id)

		# Calculate the TF-IDF for each term:
		#tfidf = defaultdict(float)

		#for word in self._term_freq.keys():
		#	tfidf[word] = ( float(self._term_freq[word]) / float(self._tf_normalizer) ) * ( log(float(corpus_size) / float(1+self._doc_freq[word])) )

		#a = list(set(tfidf.values()))
		#a.sort()

		#for key,value in sorted(tfidf.items(), key=itemgetter(1)):
			#if value > 0: break
		#	handle.write(key + ' ' + str(value) + '\n')
		#	self._stopwords.append(key)

		threshold_upper = threshold[lang_id] * self._num_docs

		for word in self._doc_freq.keys():
			if (self._doc_freq[word] >= threshold_upper):
				self._stopwords.append(word)
				handle.write(word+'\n')
			else:
				self._vocablist.append(word)

		# for key,value in sorted(self._doc_freq.items(),key=itemgetter(1)):
		# 	handle.write(key + ' ' + str(value) + '\n')

		handle.close()

		# self._doc_freq.plot()


	def assign_doc_tokens(self, vocabulary):

		for doc_id in range(len(self._doc_strings)):

			new_doc = []
			new_string = []
			new_tokenlist = []

			initial = self._doc_strings[doc_id][0]
			lang_id = initial[initial.index('#'):]

			for ii in range(len(self._doc_strings[doc_id])):
				token = self._doc_strings[doc_id][ii]

				if (token in vocabulary._vocab.keys()):

					word_id = vocabulary._vocab[token]
					random_choose	= randint(0,len(vocabulary._word_path_id[word_id])-1)
					random_path_id	= vocabulary._word_path_id[word_id][random_choose]
					new_doc.append(random_path_id)
					new_string.append(token)
					self._num_tokens[lang_id] += 1

					new_tokenlist.append(word_id)

			self._doc_tokens[doc_id]	= new_doc
			self._doc_strings[doc_id]	= new_string
			self._doc_word_id[doc_id]	= new_tokenlist



	def write_stat(self, num_topics, num_iter, alpha, beta, output_dir):

		handle = open(output_dir+'/statistics.txt', 'w')

		handle.write('----------\n')
		handle.write('Model:\n - Tree-based dictionary priors.\n')

		handle.write('----------\n')
		handle.write('Size of vocabulary:\n - %d\n' % (len(self._vocablist)))

		handle.write('----------\n')
		handle.write('Number of documents in each language:\n - %d\n' % self._num_docs)

		handle.write('----------\n')
		handle.write('Number of tokens in each language:\n')
		total = 0
		for lang_id in self._num_tokens.keys():
			total += self._num_tokens[lang_id]
			handle.write(' - %s: %d\n' % (lang_id, self._num_tokens[lang_id]))
		handle.write(' - total: %d\n' % (total))

		handle.write('----------\n')
		handle.write('Number of topics:\n - %d\n' % num_topics)

		handle.write('----------\n')
		handle.write('Number of iterations:\n - %d\n' % num_iter)

		handle.write('----------\n')
		handle.write('Stopword: ')
		if self._stopwords_dir == '': handle.write('\n - Using stopword lists according to the corpus.\n')
		else: handle.write('\n - Using fixed stopword lists from: %s\n' % self._stopwords_dir)

		handle.write('----------\n')
		handle.write('alpha:\n - %0.2f\n' % alpha)

		handle.write('----------\n')
		handle.write('beta: ')
		for ii in beta: handle.write('\n - %0.2f' % ii)	
		handle.write('\n')	

		handle.close()










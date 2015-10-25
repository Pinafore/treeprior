from common import *


"""""""""""""""""""""""""""""""""""
Sampler
"""""""""""""""""""""""""""""""""""

class Sampler:

	def __init__(self, num_iterations, num_topics, vocabulary, corpus, output_dir, alpha, beta,
				language_list=[TAG_EN,TAG_TR,TAG_ZH], rand_stub=None):

		self._num_iterations	=	num_iterations
		self._num_topics		=	num_topics
		self._lhood 			=	[]
		self._time 				=	[]
		self._language_list		=	language_list
		self._doc_tokens		=	corpus._doc_tokens
		self._doc_strings		=	corpus._doc_strings
		self._doc_word_id		=	corpus._doc_word_id
		self._rand_stub 		= 	rand_stub
		self._vocabulary		=	vocabulary
		self._beta				=	beta
		self._alpha				=	alpha
		self._state				=	State(self._num_topics, self._alpha, self._beta)
		self._output_dir		=	output_dir

		self._state.initialize(self._doc_tokens, self._doc_strings, self._doc_word_id, self._vocabulary)


	def run_sampler(self):

		handle = open(self._output_dir+'/iterations.txt', 'w')
		handle2 = open(self._output_dir+'/iterations-lhood-for-latex.txt', 'w')
		handle3 = open(self._output_dir+'/iterations-time-for-latex.txt', 'w')

		for ii in range(self._num_iterations):

			print("Iteration %i" % ii)

			start = time.time()


			for doc_id in range(len(self._doc_tokens)):

				for token_id in range(len(self._doc_tokens[doc_id])):

					word_id 		=	self._doc_word_id[doc_id][token_id]
					token_path_id	=	self._doc_tokens[doc_id][token_id]
					token_path		=	self._vocabulary._path_edge_set[token_path_id]
					all_paths_id	=	self._vocabulary._word_path_id[word_id]

					self._state.change_state(doc_id, token_id, token_path, UNASSIGNED, token_path_id)

					[bucket_s,bucket_r,bucket_q] = \
							self._state.get_all_buckets(doc_id, word_id, self._num_topics, all_paths_id, self._vocabulary)
					[new_topic_id, new_path_id, new_path] = \
							self.sample_new_topic_sparse(bucket_s, bucket_r, bucket_q, doc_id, all_paths_id)

					self._doc_tokens[doc_id][token_id] = new_path_id
					self._state.change_state(doc_id, token_id, new_path, new_topic_id, new_path_id)

			total = time.time() - start
			lhood = self.lhood()
			print("Iteration %i, likelihood %f, %0.5f seconds" % (ii, lhood, total))
			handle.write("Iteration %i, likelihood %f, %0.5f seconds\n" % (ii, lhood, total))
			handle2.write('(%d,%f)\n' % (ii,lhood))
			handle3.write('(%d,%0.5f)\n' % (ii,total))

		handle.close()
		handle2.close()
		handle3.close()


	def sample_new_topic_sparse(self, bucket_s, bucket_r, bucket_q, doc_id, all_paths_id):

		energy = random() * (bucket_s + bucket_r + bucket_q)

		# Sample from bucket s
		if energy < bucket_s:
			for topic_id in range(self._num_topics):
				for path_id in all_paths_id:
					path		=	self._vocabulary._path_edge_set[path_id]
					consume		=	self._alpha * self._state._s_lambda[path_id]
					consume		/=	self._state.get_normalizer(topic_id, path)
					energy		-=	consume
					if energy	<= 	0: return topic_id, path_id, path

		else: energy -= bucket_s

		# Sample from bucket r
		if energy < bucket_r:
			for topic_id in range(self._num_topics):
				for path_id in all_paths_id:
					path		=	self._vocabulary._path_edge_set[path_id]
					consume		=	self._state._docs[doc_id][topic_id] * self._state._s_lambda[path_id]
					consume		/=	self._state.get_normalizer(topic_id, path)
					energy		-=	consume
					if energy	<= 	0: return topic_id, path_id, path

		else: energy -= bucket_r

		# Sample from bucket q
		for topic_id in range(self._num_topics):
			for path_id in all_paths_id:
				path		=	self._vocabulary._path_edge_set[path_id]
				consume		=	(self._alpha+self._state._docs[doc_id][topic_id]) * self._state.get_observation(topic_id, path, path_id)
				consume		/=	self._state.get_normalizer(topic_id, path)
				energy		-=	consume
				if energy	<= 	0: return topic_id, path_id, path

		return topic_id, path_id, path

	def sample_new_topic(self, distribution):

		if self._rand_stub: cutoff = self._rand_stub()
		else: cutoff = random()

		if cutoff==-1: cutoff = random()
		normalizer = float(sum(distribution.values()))

		current = 0
		for i in distribution:
			assert(distribution[i] > 0)
			current += float(distribution[i]) / normalizer
			if current >= cutoff:
				return i%self._num_topics, int(i/self._num_topics)
		print("Didn't choose anything: ", cutoff, current)



	def lhood(self):

		likelihood = self.doc_likelihood() + self.topic_likelihood()
		return likelihood

	def doc_likelihood(self):

		val = self._state._doc_prior_lhood
		for doc_id in self._state._docs:
			val += sum(self._state._docs[doc_id]._sum_gamma)
			val -= lgammln(sum(self._state._docs[doc_id]._sum_sum))
		return val

	def topic_likelihood(self):
		
		val	= self._state._topic_prior_lhood
		for topic_id in range(self._num_topics):
			val += sum(self._state._topics[topic_id]._sum_gamma.values())
			val -= lgammln(sum(self._state._topics[topic_id]._sum_sum.values()))
		return val


	def report(self, output_dir, language, limit=15):

		if (not os.path.exists(output_dir)): os.mkdir(output_dir)

		# Report topics:
		for lang_id in language:
			topic_dir = output_dir + '/topics-' + lang_id + '.txt'
			handle = open(topic_dir, 'w')
			for topic_id in range(self._num_topics):
				handle.write("------------\nTopic %i\n------------\n" % (topic_id))
				word = 0
				for path in self._state._topics[topic_id].most_common():
					arr_id = path[0][1]
					if (type(arr_id) is str) and ('#'+lang_id in arr_id):
						handle.write("%0.2f\t\t%0.2f\t%s\n" % \
										(self._state._topics[topic_id]._prior[path[0]],
										self._state._topics[topic_id][path[0]],
										arr_id))
						word += 1
						if word > limit: break
			handle.close()



"""""""""""""""""""""""""""""""""""
State
"""""""""""""""""""""""""""""""""""

class State:

	def __init__(self, num_topics, alpha, beta):

		self._docs		=	defaultdict(Multinomial)
		self._topics	=	defaultdict(Multinomial)
		self._assigns	=	dict()
		self._alpha		=	alpha
		self._beta		=	beta
		self._num_docs	=	0
		self._num_nodes	=	0
		self._num_topics=	num_topics

		self._doc_prior_lhood	=	0
		self._topic_prior_lhood	=	0

		self._bucket_prior	=	defaultdict(float)
		self._s_lambda		=	defaultdict(float)



	def initialize(self, doc_tokens, doc_strings, doc_word_id, vocabulary):

		self._num_docs	=	len(doc_tokens)
		self._num_nodes	=	vocabulary._current_node_id
		self._num_edges	=	len(vocabulary._edges)
		self._num_paths	=	vocabulary._current_path_id-1

		self.initialize_docs()
		self.initialize_topics(vocabulary)

		self.initialize_assigns(doc_tokens, doc_strings, doc_word_id, vocabulary)
		self.initialize_prior_likelihood()


	def initialize_docs(self):


		for doc_id in range(self._num_docs):

			self._docs[doc_id] = Multinomial(self._alpha, self._num_topics)
			self._docs[doc_id]._sum_prior = [(self._alpha * self._num_topics) for x in range(self._num_topics)]
			self._docs[doc_id]._prior = [self._alpha for x in range(self._num_topics)]
			self._docs[doc_id]._sum_sum = self._docs[doc_id]._prior
			self._docs[doc_id]._sum_gamma = [0 for x in range(self._num_topics)]

			for topic_id in range(self._num_topics):

				self._docs[doc_id][topic_id] = 0
				self._docs[doc_id]._sum_gamma[topic_id] = lgammln(self._docs[doc_id]._prior[topic_id])


	def initialize_topics(self, vocabulary):


		for topic_id in range(self._num_topics):

			self._topics[topic_id] = Multinomial(self._beta, self._num_edges)
			self._topics[topic_id]._sum_count = [0 for x in range(vocabulary._current_node_id)]
			self._topics[topic_id]._sum_prior = [0 for x in range(vocabulary._current_node_id)]
			self._topics[topic_id]._prior = defaultdict(float)
			self._topics[topic_id]._sum_gamma = defaultdict(float)
			self._topics[topic_id]._sum_sum = defaultdict(float)

			for edge in vocabulary._edges:

				self._topics[topic_id][edge] = 0

				node_id = edge[0]
				arr_id = edge[1]

				if (type(arr_id) is int):
					group_size = len(vocabulary._treevocab[arr_id])
					self._topics[topic_id]._prior[edge] = group_size * self._beta[0]
					self._topics[topic_id]._sum_prior[node_id] += group_size * self._beta[0]
					self._topics[topic_id]._sum_sum[edge] = self._topics[topic_id]._prior[edge] + 0
					self._topics[topic_id]._sum_gamma[edge] = lgammln(self._topics[topic_id]._sum_sum[edge])

				elif (type(arr_id) is str):
					if (node_id == 0):
						self._topics[topic_id]._prior[edge] = self._beta[0]
						self._topics[topic_id]._sum_prior[node_id] += self._beta[0]
						self._topics[topic_id]._sum_sum[edge] =	self._topics[topic_id]._prior[edge] + 0
						self._topics[topic_id]._sum_gamma[edge] = lgammln(self._topics[topic_id]._sum_sum[edge])
					else:
						self._topics[topic_id]._prior[edge] = self._beta[1]
						self._topics[topic_id]._sum_prior[node_id] += self._beta[1]
						self._topics[topic_id]._sum_sum[edge] = self._topics[topic_id]._prior[edge] + 0
						self._topics[topic_id]._sum_gamma[edge] = lgammln(self._topics[topic_id]._sum_sum[edge])


		# Since all the topic has the same path priors,
		# we can just use the first topic (topic 0) to initialize the bucket.
		for word_id in range(len(vocabulary._vocab)):
			all_paths_id = vocabulary._word_path_id[word_id]
			summation = 0.0
			for path_id in all_paths_id:
				numerator 	= 1.0
				denominator = 1.0
				path = vocabulary._path_edge_set[path_id]
				for edge in path:
					numerator *= self._topics[0]._prior[edge]
					denominator *= self._topics[0]._sum_prior[edge[0]]
				summation += float(numerator) / float(denominator)
				self._s_lambda[path_id] = float(numerator)
			self._bucket_prior[word_id] = self._alpha * self._num_topics * summation
			



	def initialize_assigns(self, doc_tokens, doc_strings, doc_word_id, vocabulary):

		for doc_id in range(self._num_docs):

			num_tokens = len(doc_tokens[doc_id])

			for token_id in range(num_tokens):

				path_id = doc_tokens[doc_id][token_id]
				word_id = doc_word_id[doc_id][token_id]

				# Assign a random topic to the token:
				random_topic_id = randint(0, self._num_topics-1)
				self._assigns[(doc_id,token_id)] = random_topic_id
				assert random_topic_id >= 0, "Cannot initialize with a unknown topic."

				# Update the distribution
				token_path = vocabulary._path_edge_set[path_id]
				self.change_state(doc_id, token_id, token_path, random_topic_id, path_id)



	def initialize_prior_likelihood(self):

		# Document Likelihood (part A in my lab note)
		alpha_sum =	self._alpha * self._num_topics
		self._doc_prior_lhood	+=	lgammln(alpha_sum) * self._num_docs
		self._doc_prior_lhood	-=	self._num_topics * lgammln(self._alpha) * self._num_topics


		# Topic Likelihood (part A in my lab note)
		beta_sum = sum(self._topics[0]._sum_prior)
		self._topic_prior_lhood	+=	self._num_topics * lgammln(beta_sum)
		cache =	0.0
		for path in self._topics[0].keys():
			cache += lgammln(self._topics[0]._prior[path])
		self._topic_prior_lhood	-=	self._num_topics * cache



	def change_state(self, doc_id, token_id, token_path, topic_id, path_id):

		if topic_id == UNASSIGNED:

			old_topic = self._assigns[(doc_id, token_id)]
			# Update doc-topic distribution
			self._docs[doc_id][old_topic]			-=	1
			self._docs[doc_id]._sum_count			-=	1
			self._docs[doc_id]._sum_sum[old_topic]	-=	1
			self._docs[doc_id]._sum_gamma[old_topic] =	lgammln(self._docs[doc_id]._sum_sum[old_topic])
			# Update topic-path distribution
			self._topics[old_topic]._non_zero[path_id]	-=	1
			if self._topics[old_topic]._non_zero[path_id] <= 0:
				del self._topics[old_topic]._non_zero[path_id]
			for segment in token_path:
				node_id = segment[0]
				self._topics[old_topic][segment]			-=	1
				self._topics[old_topic]._sum_count[node_id]	-=	1
				self._topics[old_topic]._sum_sum[segment]	-=	1
				self._topics[old_topic]._sum_gamma[segment] = 	lgammln(self._topics[old_topic]._sum_sum[segment])
			del self._assigns[(doc_id, token_id)]

		else:
			# Update doc-topic distribution
			self._docs[doc_id][topic_id]			+=	1
			self._docs[doc_id]._sum_count			+=	1
			self._docs[doc_id]._sum_sum[topic_id] 	+= 	1
			self._docs[doc_id]._sum_gamma[topic_id] = 	lgammln(self._docs[doc_id]._sum_sum[topic_id])
			# Update topic-path distribution
			self._topics[topic_id]._non_zero[path_id]		+=	1
			for segment in token_path:
				node_id = segment[0]
				self._topics[topic_id][segment]				+=	1
				self._topics[topic_id]._sum_count[node_id] 	+= 	1
				self._topics[topic_id]._sum_sum[segment] 	+= 	1
				self._topics[topic_id]._sum_gamma[segment] 	= 	lgammln(self._topics[topic_id]._sum_sum[segment])
			self._assigns[(doc_id, token_id)]		=	topic_id


	def get_new_distribution(self, doc_id, all_paths):

		distribution = {}

		for path_id in range(len(all_paths)):
			for kk in range(self._num_topics):
				serial_kk = kk+self._num_topics*path_id
				distribution[serial_kk] = self._docs[doc_id].prob_doc(kk)
				for segment in all_paths[path_id]:
					distribution[serial_kk] *=	self._topics[kk].prob_topic(segment)

		return distribution


	def get_all_buckets(self, doc_id, word_id, num_topics, all_paths_id, vocabulary):

		bucket_r = 0.0
		bucket_q = 0.0

		# Calculate the bucket s
		bucket_s = self._bucket_prior[word_id]

		# Calculate the bucket r:
		for topic_id in range(num_topics):
			if (self._docs[doc_id][topic_id] == 0):
				continue
			numerator = self._docs[doc_id][topic_id]
			for path_id in all_paths_id:
				path = vocabulary._path_edge_set[path_id]
				bucket_r += (self._s_lambda[path_id]/self.get_normalizer(topic_id,path))

		# Calculate the bucket q:
		for topic_id in range(num_topics):
			for path_id in all_paths_id:
				if path_id not in self._topics[topic_id]._non_zero.keys():
					continue
				path = vocabulary._path_edge_set[path_id]
				bucket_q += (self.get_observation(topic_id, path, path_id)*(self._alpha+self._docs[doc_id][topic_id]))\
																		/ self.get_normalizer(topic_id, path)


		return bucket_s, bucket_r, bucket_q



	def get_normalizer(self, topic_id, path):

		ret = 1.0
		for edge in path:
			ret *= (self._topics[topic_id]._sum_prior[edge[0]] + self._topics[topic_id]._sum_count[edge[0]])

		return ret

	def get_observation(self, topic_id, path, path_id):
		
		ret = 1.0
		for edge in path:
			ret *= (self._topics[topic_id]._sum_sum[edge])

		return ret - self._s_lambda[path_id]





"""""""""""""""""""""""""""""""""""
Multinomial
"""""""""""""""""""""""""""""""""""

class Multinomial(Counter):

	def __init__(self, prior, dim):

		self._dim		=	dim
		self._prior		=	prior
		self._sum_prior	=	0
		self._sum_count	=	0
		self._sum_gamma	=	0
		self._sum_sum	=	0

		self._non_zero	= defaultdict(int)

	def prob_doc(self, key):

		numerator = self._prior[key]
		numerator += list(self.values())[key]
		denominator = self._sum_prior[key] + self._sum_count

		return numerator / denominator

	def prob_topic(self, key):

		numerator = self._prior[key] + self[key]
		denominator = self._sum_prior[key[0]] + self._sum_count[key[0]]

		return numerator / denominator

from common import *


"""""""""""""""""""""""""""""""""""
VocabBuilder
"""""""""""""""""""""""""""""""""""

class VocabBuilder:

	def __init__(self, input_dir, stopwords, vocablist):

		# Initialize
		# We maintain two lists for vocabulary:
		# self._treevocab stores the relations of words together
		# tempvocab is just a big list of all words, without their relations
		self._stopwords 		= stopwords
		self._treevocab 		= {}
		self._treevocab[0]		= []
		self._edges				= []
		self._word_path_id		= defaultdict(list)
		self._path_edge_set		= defaultdict(list)
		self._current_node_id	= 1
		self._current_path_id	= 0
		self._vocab				= defaultdict(int)
		self._num_vocab			= 0
		
		# Load in Wiktionary
		# Use dict() for a dictionary
		# Key is the internal node number,
		# Value is the list of the word under that internal node
		handle		= open(input_dir, 'r')
		temptoken	= []
		tempvocab	= set()

		for line in handle:

			parsed	=	line.split(':')
			parsed	=	[x.strip() for x in parsed]

			if not set(parsed).intersection(vocablist): continue

			if (len(parsed) == 1)\
				and (len(parsed[0][:-3])>=MIN_LENGTH)\
				and (parsed[0] not in self._stopwords):

				# current_word = parsed[0]
				# self._treevocab[0].append(current_word)
				# self._word_path[current_word].append([(0,current_word)])
				# tempvocab.add(current_word)
				# self._edges.append((0,current_word))


				current_word = parsed[0]
				tempvocab.add(current_word)
				self._treevocab[0].append(current_word)
				self._word_path_id[current_word].append(self._current_path_id)
				self._path_edge_set[self._current_path_id].append((0,current_word))
				self._current_path_id += 1
				self._edges.append((0,current_word))

				temptoken.append(current_word)
				

			else:
				actual_number	=	0
				actual_parsed	=	[]

				for ii in range(len(list(set(parsed)))):

					current_word = parsed[ii]

					if ('#cmn' in current_word):
						if (len(current_word[:-4]) >= MIN_LENGTH_CMN) and (current_word not in self._stopwords):
							# actual_number += 1
							# newpath	= [(0,self._current_node_id),(self._current_node_id,current_word)]
							# self._word_path[current_word].append(newpath)
							# actual_parsed.append(current_word)
							# self._paths.append((self._current_node_id,current_word))

							actual_number += 1
							newpath = [(0,self._current_node_id),(self._current_node_id,current_word)]
							self._word_path_id[current_word].append(self._current_path_id)
							self._path_edge_set[self._current_path_id].append((0,self._current_node_id))
							self._path_edge_set[self._current_path_id].append((self._current_node_id,current_word))
							self._current_path_id += 1
							self._edges.append((self._current_node_id,current_word))
							actual_parsed.append(current_word)

							temptoken.append(current_word)

					else:
						if (len(current_word[:-3]) >= MIN_LENGTH) and (current_word not in self._stopwords):

							actual_number += 1
							newpath = [(0,self._current_node_id),(self._current_node_id,current_word)]
							self._word_path_id[current_word].append(self._current_path_id)
							self._path_edge_set[self._current_path_id].append((0,self._current_node_id))
							self._path_edge_set[self._current_path_id].append((self._current_node_id,current_word))
							self._current_path_id += 1
							self._edges.append((self._current_node_id,current_word))
							actual_parsed.append(current_word)

							temptoken.append(current_word)


				if (actual_number > 0) and (actual_parsed is not []):

					self._edges.append((0,self._current_node_id))
					self._treevocab[self._current_node_id] = actual_parsed
					self._treevocab[0].append(self._current_node_id)
					self._current_node_id += 1
					tempvocab.update(actual_parsed)


		handle.close()

		self._edges = list(set(self._edges))
		tempvocab = list(tempvocab)

		for pos in range(len(tempvocab)):
			word_str = tempvocab[pos]
			self._vocab[word_str] = pos
			list_of_path_id = self._word_path_id[word_str]
			self._word_path_id[pos] = list_of_path_id
			del self._word_path_id[word_str]




		print(' - len(temptoken) = ', len(temptoken))
		print(' - len(set(temptoken)) = ', len(set(temptoken)))
		print(' - len(tempvocab) = ', len(tempvocab))
		print(' - len(self._word_path_id) = ', len(self._word_path_id))

		print('Dictionary loaded. Number of words: ', len(tempvocab))
		print('Paths created. Number of path edges: ', len(self._edges))




from VocabBuilder	import *
from CorpusLoader	import *
from Sampler		import *
from common			import *


if __name__ == "__main__":

	# Parse the arguments passed
	argparser = argparse.ArgumentParser()
	argparser.add_argument("--doc_dir", help="Where we read the source documents",
							type=str,	default="../corpus/TED2013/all", required=False)
	argparser.add_argument("--language", help="The language we use",
							type=list,	default=[TAG_EN,TAG_TR,TAG_ZH], required=False)  
	argparser.add_argument("--vocab_size", help="Size of vocabulary",
							type=int,	default=1000, required=False)
	argparser.add_argument("--num_topics", help="Number of topics",
							type=int,	default=20, required=False)
	argparser.add_argument("--num_iterations", help="Number of iterations",
							type=int,	default=100, required=False)
	argparser.add_argument("--wiki", help="where to load wiktionary",
							type=str,	default="vocabulary.txt", required=False)
	argparser.add_argument("--output", help="where to write the report",
							type=str,	default="./report", required=False)
	argparser.add_argument("--limit", help="how many documents in each language should be loaded",
							type=int,	default=-1, required=False)
	argparser.add_argument("--stop", help="use preloaded stopword lists",
							type=str,	default='', required=False)
	argparser.add_argument("--alpha", help="document priors",
							type=float,	default=1.0, required=False)
	argparser.add_argument("--beta", help="tree priors",
							type=list,	default=[0.01,100], required=False)
	args = argparser.parse_args()


	## Detect cache files:
	if len(os.listdir(CACHE_DIR))==0 or len(os.listdir(CACHE_DIR))==1:

		# Load in the corpus
		start = time.time()
		loader = CorpusLoader(args.doc_dir, args.stop, args.limit, language_list=args.language)
		loader.scan_corpus()
		print('Corpus loaded. Time passed: ', time.time()-start)

		# Load in the dictionary:
		start = time.time()
		builder = VocabBuilder(args.wiki, loader._stopwords, loader._vocablist)
		print('Dictionary loaded. Time passed: ', time.time()-start)

		# Assign document token indices:
		start = time.time()
		loader.assign_doc_tokens(builder)
		print('Document token IDs assigned. Time passed: ', time.time()-start)

		pickle.dump( builder, open( CACHE_DIR+'/VocabBuilder_builder.p', 'wb' ) )
		pickle.dump( loader, open( CACHE_DIR+'/CorpusLoader_loader.p', 'wb' ) )

		# Write the statistics:
		loader.write_stat(args.num_topics, args.num_iterations, args.alpha, args.beta, args.output)
		


	else:
		print('Cache files detected: \n', os.listdir(CACHE_DIR))
		builder	= pickle.load( open( CACHE_DIR+'/VocabBuilder_builder.p', 'rb' ) )
		loader	= pickle.load( open( CACHE_DIR+'/CorpusLoader_loader.p', 'rb' ) )

		# Write the statistics:
		loader.write_stat(args.num_topics, args.num_iterations, args.alpha, args.beta, args.output)



	## Initialize the sampler
	start = time.time()
	sampler = Sampler(args.num_iterations, args.num_topics, builder, loader, output_dir=args.output, alpha=args.alpha, beta=args.beta)
	print('Sampler initialized. Time passed: ', time.time()-start)

	## Run the sampler
	sampler.run_sampler()

	## Report the result
	sampler.report(args.output, args.language)




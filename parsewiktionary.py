
import re

TAG_EN  = '#en'
TAG_ZH  = '#cmn'
TAG_TR  = '#tr'
TAG_UZ  = '#uz'
TAG_HA  = '#ha'

singleton = []

def include_chinese(part):
	"""
	Check if a string contains Chinese.
	If it does contain Chinese, then return all the Chinese characters in one string.
	This function does not discriminate simplified and traditional Chinese.
	"""

	stripped = ''
	for ch in part:
		if ch.isdigit(): return ''
		elif ord(ch) < 0x4e00 or ord(ch) > 0x9fff: stripped += ''
		else: stripped += ch
	return stripped


def parse_translation(language, line):
	"""
	Given a language and a line from Wiktionay XML,
	this function returns a list, consisting of all the translations of this language.
	Due to difficulties in parse Chinese translation,
	this function discriminates Chinese and all other languages.
	"""

	return_string = []
	groups = re.split(',', line)

	# Chinese
	if language == TAG_ZH:
		for each in groups:
			minor	= each.split('|')
			for ii in range(len(minor)):
				part = include_chinese(minor[ii])
				if (part != ''): return_string.append(part+language)
		return return_string

	# Turkish, Uzbek and Hausa
	else:
		code = language[1:]
		for each in groups:
			minor	= each.split('|')
			mode	= False
			for ii in range(len(minor)):
				if (code in minor[ii]): mode = True
				elif (mode):
					if ('}}' in minor[ii]): ending = minor[ii].index('}}')
					else: ending = len(minor[ii])
					if (minor[ii][:ending] != ''):
						return_string.append((minor[ii][:ending].replace('[', '')).replace(']', '').lower() + language)
					mode = False
				elif ('alt=' in minor[ii]) & ('alt=;' not in minor[ii]):
					if ('}}' in minor[ii]): ending = minor[ii].index('}}')
					else: ending = len(minor[ii])
					return_string.append((minor[ii][4:ending].replace('[', '')).replace(']', '').lower() + language)
		return return_string


def parse_wiktionary(input_dir, output_dir):
	"""
	input_dir should be the directory of the Wiktionary XML file.
	output_dir is the directory of the output file.
	"""

	handle      = open(input_dir, 'r')
	writer      = open(output_dir, 'w')
	loadtrans   = False
	loadtitle	= False
	title       = ''
	parsed		= []

	a = 0

	for line in handle:

		# Mark the start of a new page (exclude irrelevant pages)
		if ('<title>' in line) & (':' not in line):
			title	= (re.split('<title>|</title>', line))[1]
			loadtitle = True

		# Pass the non-English words
		elif ('==English==' in line) & (loadtitle):
			loadtrans = True

		elif (('* Turkish:' in line) or ('*: Turkish:' in line)) & ('t-needed' not in line):
			parsed += parse_translation(TAG_TR, line)
		elif (('* Uzbek:' in line) or ('*: Uzbek:' in line)) & ('t-needed' not in line):
			parsed += parse_translation(TAG_UZ, line)
		elif (('* Hausa:' in line) or ('*: Hausa:' in line)) & ('t-needed' not in line):
			parsed += parse_translation(TAG_HA, line)
		elif (('* Mandarin:' in line) or ('*: Mandarin:' in line)) & ('t-needed' not in line):
			parsed += parse_translation(TAG_ZH, line)

	 

		elif ('</page>' in line) & (loadtrans):
			if (len(parsed) == 0):
				if (title.lower() not in singleton):
					singleton.append(title.lower())
					writer.write(title.lower()+TAG_EN)
					writer.write('\n')
					loadtrans	= False
					loadtitle	= False
					parsed		= []
			else:
				writer.write(title.lower()+TAG_EN)
				for member in set(parsed): writer.write(':' + member.lower())
				writer.write('\n')
				loadtrans	= False
				loadtitle	= False
				parsed		= []

			print(a)
			a += 1
			

	handle.close()
	writer.close()


if __name__ == "__main__":

	wiktionary_dir  = '../dataset/enwiktionary-latest-pages-articles.xml'
	vocabulary_dir  = 'vocabulary.txt'
	parse_wiktionary(wiktionary_dir, vocabulary_dir)




















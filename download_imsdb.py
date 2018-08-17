import os
import sys
import argparse
from requests_html import HTMLSession
import json
import re

SCRIPT_LIST_URL = "http://www.imsdb.com/all scripts/"
SCRIPT_INFO_URL = "http://www.imsdb.com/Movie Scripts/"

MAIN_URL = "http://www.imsdb.com"
GENRE_URI = "/genre/"
SCRIPT_URI = "/scripts/"

SCRIPT_INFO_CLASS = ".script-details"
SCRIPT_SRC_CLASS = ".scrtext"

SCRIPTS_INFO_FILENAME = "scripts_info.json"

PROGRESS_BAR_LENGTH = 50

# add arguments and parse
parser = argparse.ArgumentParser()
parser.add_argument("path", help="path of directory where the data will be saved")
parser.add_argument("format", help="True or False, if True the scripts will be formatted for machine readability")
args = parser.parse_args()

# add slash to path if not already there
save_path = args.path
if save_path[-1] != "/":
	save_path += "/"

if not os.path.isdir(save_path):
	sys.exit("directory does not exist")


##
# get script list page
print("getting script list...")

session = HTMLSession()
try:
	r = session.get(SCRIPT_LIST_URL)
except:
	sys.exit("failed to get script list")

# get all links on script list page
links = r.html.absolute_links
script_titles = []

# get script names from link urls
for link_url in links:
	if SCRIPT_INFO_URL in link_url:
		# take away script info url and ".html" at end
		script_titles.append(link_url[len(SCRIPT_INFO_URL):-5])

print("found {} scripts".format(len(script_titles)))


##
# get script info and download script
print("downloading scripts...")

scripts_info = {}

# set up progress bar
n_downloaded = 0
n_failed = 0
n_bars = 0

sys.stdout.write("[{}]".format("_" * PROGRESS_BAR_LENGTH))
sys.stdout.flush()
sys.stdout.write("\b" * (PROGRESS_BAR_LENGTH + 1))

for title in script_titles:
	# get info page
	try:
		r_info = session.get(SCRIPT_INFO_URL + title + ".html")

		info_links = r_info.html.find(SCRIPT_INFO_CLASS, first=True).links

		# get genres and script url
		genres = []
		script_url = MAIN_URL + SCRIPT_URI + title
		for link_url in info_links:
			if GENRE_URI in link_url:
				genres.append(link_url[len(GENRE_URI):])
			elif SCRIPT_URI in link_url:
				script_url = MAIN_URL + link_url

		# get script page
		r_script = session.get(script_url)

		script_src = r_script.html.find(SCRIPT_SRC_CLASS, first=True)

		if script_src == None or script_src.full_text == None:
			n_failed += 1
			continue


		formatted_script = script_src.full_text
		if args.format:
			# swaps tabs for spaces and deletes carriage return
			formatted_script = re.sub("\t", " ", formatted_script)
			formatted_script = re.sub("\r", "", formatted_script)
			# removes multiple spaces
			formatted_script = re.sub("  +", " ", formatted_script)
			# removes spaces after and before next lines
			formatted_script = re.sub("\n +", "\n", formatted_script)
			formatted_script = re.sub("  \n+", "\n", formatted_script)
			# removes more than two next lines
			formatted_script = re.sub("\n\n+", "\n\n", formatted_script)
			# removes line breaks in the middle of text (single next lines)
			formatted_script = re.sub("(?<=.)\n(?=.)", " ", formatted_script)
			formatted_script = formatted_script.strip()

		# save script to file
		script_file = open(save_path + title + ".txt", "w")
		script_file.write(formatted_script)
		script_file.close()

		# add script info
		scripts_info[title] = { "filename": title + ".txt",
														"genres": genres }
	except:
		n_failed += 1

	# update progress bar
	n_downloaded += 1
	n_bars_new = int(round((n_downloaded + n_failed) / len(script_titles) * PROGRESS_BAR_LENGTH))
	sys.stdout.write("#" * (n_bars_new - n_bars))
	sys.stdout.flush()
	n_bars = n_bars_new

print("done, {} failed".format(n_failed))

# save script info
scripts_info_file = open(save_path + SCRIPTS_INFO_FILENAME, "w")
json.dump(scripts_info, scripts_info_file)
scripts_info_file.close()


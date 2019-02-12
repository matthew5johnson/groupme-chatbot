import os
import json
import sys
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from flask import Flask, request
import re
import pymysql

import scrape
import message


app = Flask(__name__)



###################################### Instructions: 
###################################### Find/replace for 'season', comment out/comment in standings command for regular season only, add features to help message

@app.route('/', methods=['POST'])
def webhook():
	data = request.get_json()
	#####     Sniffing for @bot     #####
	if '@bot' in data['text']:
		sender = data['user_id']
		text = data['text']
		# sys.stdout.write('sender: {} | text: {}'.format(sender,text))
		parse(sender, text)
		return('ok',200)

	#####     Sniffing for @testing     #####
	elif '@testing' in data['text']:
		# Sends us into a play function (sandbox_testing) that feeds into a send message function aimed at File Sharing group
		# text = data['text']
		# sys.stdout.write('sent into testing environment')
		# sandbox_testing(text)
		games_over = scrape.update_scores(1, 1)
		text = message.get_scores(1, 2, games_over)
		message_to_sandbox(text)

		return('ok',200)
	else: return('ok',200)

def database_access(table, command):
	con = pymysql.connect(host=os.environ['DB_ACCESS_HOST'], user=os.environ['DB_ACCESS_USER'], password=os.environ['DB_ACCESS_PASSWORD'], database=os.environ['DB_ACCESS_DATABASE'])
	cur = con.cursor()


	##########  SETTINGS
	if table == 'settings':
		cur.execute("SELECT settings_rbvotes, settings_week FROM settings WHERE description='main';")
		settings_tuple = cur.fetchall()
		con.commit()
		con.close()
		if command == 'week':
			week = int(settings_tuple[0][1])
			return(week)
		elif command == 'rb':
			rb_votes = int(settings_tuple[0][0])
			return(rb_votes)
	
	#########   RECORDS		
	elif table == 'records':
		if command == 'all':
			# Highest single game score
			cur.execute("SELECT weekly_points, franchise, season, week, opponent FROM weekly_records WHERE type=1 ORDER BY weekly_points desc LIMIT 1;")
			weekly_highscore_tuple = cur.fetchall()
			con.commit()
			# Lowest single game score
			cur.execute("SELECT weekly_points, franchise, season, week, opponent FROM weekly_records WHERE type=2 ORDER BY weekly_points asc LIMIT 1;")
			weekly_lowcore_tuple = cur.fetchall()
			con.commit()
			# Biggest blowout
			cur.execute("SELECT weekly_margin, franchise, season, week, opponent FROM weekly_records WHERE type=3 ORDER BY weekly_margin desc LIMIT 1;")
			weekly_blowout_tuple = cur.fetchall()
			con.commit()
			# Closest game
			cur.execute("SELECT weekly_margin, franchise, season, week, opponent FROM weekly_records WHERE type=4 ORDER BY weekly_margin asc LIMIT 1;")
			weekly_closest_tuple = cur.fetchall()
			con.commit()
			# Most PPG Season
			cur.execute("SELECT season_ppg, franchise, season FROM season_records WHERE type=5 ORDER BY season_ppg desc LIMIT 1;")
			season_highppg_tuple = cur.fetchall()
			con.commit()
			# Fewest PPG Season
			cur.execute("SELECT season_ppg, franchise, season FROM season_records WHERE type=6 ORDER BY season_ppg asc LIMIT 1;")
			season_lowppg_tuple = cur.fetchall()
			con.commit()
			# Most WINS
			cur.execute("SELECT season_wins, franchise, season FROM season_records WHERE type=7 ORDER BY season_wins desc LIMIT 1;")
			season_highwins_tuple = cur.fetchall()
			con.commit()
			# Fewest WINS
			cur.execute("SELECT season_wins, franchise, season FROM season_records WHERE type=8 ORDER BY season_wins asc LIMIT 1;")
			season_lowwins_tuple = cur.fetchall()
			con.commit()
			# Highest avg margin of victory
			cur.execute("SELECT season_margin, franchise, season FROM season_records WHERE type=9 ORDER BY season_margin desc LIMIT 1;")
			season_highmargin_tuple = cur.fetchall()
			con.commit()

			con.close()
			
			return(weekly_highscore_tuple, weekly_lowcore_tuple, weekly_blowout_tuple, weekly_closest_tuple, season_highppg_tuple, season_lowppg_tuple, season_highwins_tuple, season_lowwins_tuple, season_highmargin_tuple)
			# return(weekly_points, franchise, season, week, opponent)
		else: 
			return('none',200)
	else:
		con.close()
		sys.stdout.write('entered db access but no relevant command')
		return('ok',200)

# change to env variables
def database_change_week(direction):
	week = database_access('settings', 'week')
	if direction == 'plus':
		week += 1
	elif direction == 'minus':
		week -= 1

	con = pymysql.connect(host=os.environ['DB_ACCESS_HOST'], user=os.environ['DB_ACCESS_USER'], password=os.environ['DB_ACCESS_PASSWORD'], database=os.environ['DB_ACCESS_DATABASE'])
	cur = con.cursor()
	cur.execute("UPDATE settings SET settings_week=%s WHERE description='main';", (week))
	con.commit()
	con.close()
	return('Week updated to %s') % (week)

def database_remove_bob():
	rb_votes = database_access('settings', 'rb')
	rb_votes += 1

	con = pymysql.connect(host=os.environ['DB_ACCESS_HOST'], user=os.environ['DB_ACCESS_USER'], password=os.environ['DB_ACCESS_PASSWORD'], database=os.environ['DB_ACCESS_DATABASE'])
	cur = con.cursor()
	cur.execute("UPDATE settings SET settings_rbvotes=%s WHERE description='main';", (rb_votes))
	con.commit()
	con.close()
	return('Total #RB votes: %s') % (rb_votes)




def parse(sender, text):
	#### Ignore every line that the bot prints out itself
	if re.search("'@bot", text, re.I) or re.search('"@bot', text) or re.search("-----   Commands   -----", text) or re.search("1. '@bot help' = this help message", text) or re.search("2. '@bot scores' = live scores", text) or re.search("3. '@bot my score' = your live score", text) or re.search("4. '@bot (franchise) score' = enter any franchise name", text) or re.search("5. '@bot records' = record book", text) or re.search("_commands are case and space insensitive_", text) or re.search("We can add pretty much any other features you think of. Post any other cool ideas that you've got, and we'll add them to the wish list.", text) or re.search('Total #RB votes', text) or re.search('Week has been set to', text): 
		# AVOID responding to the BOT itself (in the help message)
		return('ok',200)
	# 2   ...   @bot my score 
	elif re.search('my', text, re.I) and re.search('score', text, re.I):
		franchise = get_franchise_number(sender)
		# sys.stdout.write('franchise: {} <<'.format(franchise))
		# get_data(franchise, 1)
		get_data_no_webdriver(franchise, 1)
		return('ok',200)
	# 1   ...   @bot franchise summary
	elif re.search('summary', text, re.I):
		if re.search('my', text, re.I):
			franchise = get_franchise_number(sender)
		else:
			franchise, message_type = text_id_franchise(text)
		franchise_summary(franchise)
		return('ok',200)
	
	# 3   ...   @bot all scores
	elif re.search('score', text, re.I): #re.search('all', text, re.I) and
		franchise, message_type = text_id_franchise(text)
		# get_data(franchise, message_type)
		get_data_no_webdriver(franchise, message_type)
		return('ok',200)

	elif re.search('standings', text, re.I): #re.search('all', text, re.I) and
		send_message('It\'s the postseason. Check out the playoff bracket and consolation ladder')
		# get_standings()  # <<<-- uncomment this out again for the regular season. I commented it out for postseason.
		return('ok',200)
	
	# 4   ...   @bot records
	elif re.search('record', text, re.I):
		weekly_highscore_tuple, weekly_lowcore_tuple, weekly_blowout_tuple, weekly_closest_tuple, season_highppg_tuple, season_lowppg_tuple, season_highwins_tuple, season_lowwins_tuple, season_highmargin_tuple = database_access('records', 'all')
		# message = '1. %s : %s - %s/%s vs %s' % (weekly_points, franchise, season, week, opponent)
		### Weekly
		best_game = 'Most points scored in a game:\n%s - %s (%s/%s)' % (weekly_highscore_tuple[0][0], weekly_highscore_tuple[0][1], weekly_highscore_tuple[0][2], weekly_highscore_tuple[0][3])
		worst_game = 'Fewest points in a game:\n%s - %s (%s/%s)' % (weekly_lowcore_tuple[0][0], weekly_lowcore_tuple[0][1], weekly_lowcore_tuple[0][2], weekly_lowcore_tuple[0][3])
		blowout = 'Biggest blowout:\n%s - %s (%s/%s)' % (weekly_blowout_tuple[0][0], weekly_blowout_tuple[0][1], weekly_blowout_tuple[0][2], weekly_blowout_tuple[0][3])
		closest_game = 'Closest game:\n%s - %s (%s/%s)' % (weekly_closest_tuple[0][0], weekly_closest_tuple[0][1], weekly_closest_tuple[0][2], weekly_closest_tuple[0][3])
		### Seasonal
		best_ppg = 'Most points-per-game in a season:\n%s - %s (%s)' % (season_highppg_tuple[0][0], season_highppg_tuple[0][1], season_highppg_tuple[0][2])
		fewest_ppg = 'Fewest ppg in a season:\n%s - %s (%s)' % (season_lowppg_tuple[0][0], season_lowppg_tuple[0][1], season_lowppg_tuple[0][2])
		most_wins = 'Most wins:\n%s - %s (%s)' % (season_highwins_tuple[0][0], season_highwins_tuple[0][1], season_highwins_tuple[0][2])
		high_margin = 'Largest average margin of victory:\n%s - %s (%s)' % (season_highmargin_tuple[0][0], season_highmargin_tuple[0][1], season_highmargin_tuple[0][2])
		message = "=== Modern Era Record Book ===\n-----  Week  -----\n%s\n%s\n%s\n%s\n-----  Season  -----\n%s\n%s\n%s\n%s" % (best_game, worst_game, blowout, closest_game, best_ppg, fewest_ppg, most_wins, high_margin)
		send_message(message)
		return('ok',200) 

	# 5   ...   @bot faab
	elif re.search('faab', text, re.I):
		get_faab()
		return('ok',200)

	#### Stock responses. ** Remember to add or statements to the first if test above to exclude bot responses from generating an infinite loop of responses
	
	# Get list of NFL bets
	elif re.search('bets', text, re.I):
		get_bets()
		return('ok',200)

	# help   ...   and posts response
	elif re.search('help', text, re.I):
		help_message = "All scores are scraped in real-time\n-----   Commands   -----\n'@bot help' = this help message\n--- --- ---\n1. '@bot (franchise) summary' = franchise stats\n2. '@bot scores' = live scores\n3. '@bot my score' = your live score\n4. '@bot (franchise) score' = enter any franchise name\n5. '@bot records' = record book\n6. '@bot faab' = FAAB remaining\n=====\n7. '@bot standings' = live regular season standings\n=====\nOTHER:\n'@bot bets' = spreads & O/Us\n----\nWe can add pretty much any other features you think of. Post any other cool ideas that you've got, and we'll add them to the wish list. Wishlist: n/a"
		send_message(help_message)
		return('ok',200)
	#    ...   @bot remove bob   ...   and posts vote tally
	elif re.search('remove', text, re.I) and re.search('bob', text, re.I):
		rb_message = database_remove_bob()
		send_message(rb_message)
		return('ok',200)

	## Comment this back in next year
	# elif re.search('vegas', text, re.I):
	# 	# vegas_message = get_vegas_lines(text)
	# 	# send_message(vegas_message)
	# 	get_vegas_lines(text)
	# 	return('ok',200)
	
	##### Settings from within the groupme
	# Set the week. Can only be done when '@bot advance week' is sent by me
	elif re.search('next week', text, re.I) and sender == '7435972':
		settings_message = database_change_week('plus')
		send_message(settings_message)
		return('ok',200)
	elif re.search('last week', text, re.I) and sender == '7435972':
		settings_message = database_change_week('minus')
		send_message(settings_message)
		return('ok',200)
	elif re.search('next week', text, re.I) or re.search('last week', text, re.I):
		message = '#KyleLogic'
		send_message(message)
	else: return('off topic',200)

def get_data(franchise, message_type):
	try:
		from bs4 import BeautifulSoup
		from selenium import webdriver
		from selenium.webdriver.chrome.options import Options 
		import selenium.webdriver.chrome.service as service
		season = 2018
		week = database_access('settings', 'week')
		url = 'http://games.espn.com/ffl/scoreboard?leagueId=133377&matchupPeriodId=%s&seasonId=%s' % (week, season)
		chrome_options = Options()
		chrome_options.binary_location = os.environ['GOOGLE_CHROME_BIN']
		chrome_options.add_argument('--disable-gpu')
		chrome_options.add_argument('--no-sandbox')
		chrome_options.add_argument('--headless')
		driver = webdriver.Chrome(executable_path=os.environ['CHROMEDRIVER_PATH'], chrome_options=chrome_options)
		driver.get(url)
		html = driver.page_source
		driver.close()
		soup = BeautifulSoup(html, "lxml")

		# This gives a list of franchise numbers in the order that they're matched up
		franchise_number_list = re.findall(r'(?<=id="teamscrg_)[0-9]*', str(soup)) # confirmed: this creates a list
		points_list = []
		projected_list = []

		# The if statement tests to see if the matchup is ongoing (returns true if so) or already completed (returns false if so)
		if re.search('tmTotalPts_', str(soup)):
			for i in franchise_number_list:
				points_list.append(soup.select_one('#tmTotalPts_%s' % (i)).text)
				projected_list.append(soup.select_one('#team_liveproj_%s' % (i)).text)
		else:
			points_list = re.findall(r'(?<=width="18%">)[0-9]*[.]?[0-9]', str(soup))
			projected_list = 'GAME COMPLETED'
			sys.stdout.write('nestled into a completed game. no projs')

		generate_message(franchise, message_type, franchise_number_list, points_list, projected_list)
		return('ok',200) 

	except:
		send_message('Error. Our combination of free cloud hosting + webdriver is lagging like a noob. Try a different command, or retry the same command in a few mintues.')
		return('get_data failed')


def generate_message(franchise, message_type, franchise_number_list, points_list, projected_list):
	
	#####     @bot my score     #####

	if message_type == 1:
		position = franchise_number_list.index(str(franchise))
		franchise_score = points_list[position]
		
		# Tests to see if the game is already over. 'N/A' projected list means it's over and there are no longer projections available
		if projected_list != 'GAME COMPLETED':
			franchise_proj = projected_list[position]
			sys.stdout.write(franchise_proj)
		if position % 2 == 0:
			opponent_position = position + 1
		else: 
			opponent_position = position - 1

		opponent_franchise = int(franchise_number_list[opponent_position])
		opponent_score = points_list[opponent_position]
		# sys.stdout.write('opponent score')
		
		# Tests to see if the game is already over. 'N/A' projected list means it's over and there are no longer projections available
		if projected_list != 'GAME COMPLETED':
			opponent_proj = projected_list[opponent_position]
			# sys.stdout.write(opponent_proj)

		# Test to see if the game is already over. 'N/A' projected list means it's over and there are no longer projections available
		if projected_list != 'GAME COMPLETED':
			my_ongoing_matchup = '{} - {} | proj: {}\n{} - {} | proj: {}'.format(franchise_score, get_franchise_name(franchise), franchise_proj, opponent_score, get_franchise_name(opponent_franchise), opponent_proj)
			send_message(my_ongoing_matchup)
			return('ok',200)
			# WORKED B
		else: 
			my_completed_matchup = '{} - {}\n{} - {}'.format(franchise_score, get_franchise_name(franchise), opponent_score, get_franchise_name(opponent_franchise))
			sys.stdout.write('It should send my score from last week')
			send_message(my_completed_matchup)
			return('ok',200)
			# WORKED C
	
	#####     @bot all scores     #####

	elif message_type == 2:
		week = database_access('settings', 'week')
		if projected_list != 'GAME COMPLETED':
			live_scoreboard = '*** Week %i Live Scoreboard ***\n' % week
			for i in range(len(franchise_number_list))[0::2]:
				live_scoreboard = live_scoreboard + '{} - {} | proj: {}\n{} - {} | proj: {}\n===== ===== =====\n'.format(points_list[i], get_franchise_name(int(franchise_number_list[i])), projected_list[i], points_list[i+1], get_franchise_name(int(franchise_number_list[i+1])), projected_list[i+1])
			send_message(live_scoreboard)
			return('ok',200)
		else:
			final_scoreboard = '*** Week %i Final Scoreboard ***\n' % week
			for i in range(len(franchise_number_list))[0::2]:
				final_scoreboard = final_scoreboard + '{} - {}\n{} - {}\n===== ===== =====\n'.format(points_list[i], get_franchise_name(int(franchise_number_list[i])), points_list[i+1], get_franchise_name(int(franchise_number_list[i+1])))
			send_message(final_scoreboard)
			return('ok',200)


def get_bets():
	con = pymysql.connect(host=os.environ['DB_ACCESS_HOST'], user=os.environ['DB_ACCESS_USER'], password=os.environ['DB_ACCESS_PASSWORD'], database=os.environ['DB_ACCESS_DATABASE'])
	cur = con.cursor()
	cur.execute("SELECT * FROM betting_table;")
	bets = cur.fetchall()
	con.commit()
	cur.close()
	con.close()

	message = "This week's NFL slate:\n"
	bet_length = len(bets)
	for i in range(0,bet_length):
		message = message + "{}\n".format(bets[i][0])
	send_message(message)
	return('ok',200)

def get_faab():
	try:
		from bs4 import BeautifulSoup
		from urllib.request import urlopen

		season = 2018
		faab_list = []

		for team_id in range(1,13):
			url = 'http://games.espn.com/ffl/clubhouse?leagueId=133377&teamId=%s&seasonId=%s' % (team_id, season)
			page = urlopen(url)
			page_content = page.read()
			soup = BeautifulSoup(page_content, "lxml")
			holding = re.findall(r'(?<=leagueId=133377">\$)[0-9]*', str(soup))
			faab_list.append(holding[0])
	except:
		return('error getting faab')
	########## Put into ClearDb
	con = pymysql.connect(host=os.environ['DB_ACCESS_HOST'], user=os.environ['DB_ACCESS_USER'], password=os.environ['DB_ACCESS_PASSWORD'], database=os.environ['DB_ACCESS_DATABASE'])
	cur = con.cursor()

	cur.execute("DROP TABLE temporary_faab;")
	con.commit()
	cur.execute("CREATE TABLE temporary_faab (franchise INT, faab INT, PRIMARY KEY(franchise));")
	con.commit()

	for i in range(0,12):
		cur.execute("INSERT INTO temporary_faab VALUES(%s, %s);", (i+1, faab_list[i]))
		con.commit()
	con.close()


	faab_from_db()
	return('ok',200)

def faab_from_db():
	con = pymysql.connect(host=os.environ['DB_ACCESS_HOST'], user=os.environ['DB_ACCESS_USER'], password=os.environ['DB_ACCESS_PASSWORD'], database=os.environ['DB_ACCESS_DATABASE'])
	cur = con.cursor()
	cur.execute("SELECT * FROM temporary_faab ORDER BY faab desc;")
	faab_holder = cur.fetchall()
	con.commit()
	con.close()

	faab_message = "Current FAAB Budgets:\n"
	for i in range(0,12):
		faab_message = faab_message + "{}. {}: ${}\n".format(i+1, get_franchise_name(faab_holder[i][0]), faab_holder[i][1])
	send_message(faab_message)
	return('ok',200)








def send_message(msg):
	url = 'https://api.groupme.com/v3/bots/post'
	##### Formatting wishlist: {:>8} . {:18} proj: {}   ... The error is here prob because it can't encode a list data type in the middle of a string. work with the types. .type print to console if you can't print the list itself.
	# os.environ['GROUPME_TOKEN']   ...   os.environ['SANDBOX_TOKEN']
	message = {
		'text': msg,  
		'bot_id': os.environ['GROUPME_TOKEN'] 
		}
	request = Request(url, urlencode(message).encode())
	json = urlopen(request).read().decode()
	

	# json = requests.post(url, message) # This was tossing epic urllib3.exceptions.ProtocolError: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))
	# sys.stdout.write('made it to send_message function. This was passed {} << '.format(msg))
	return('ok',200)

def get_franchise_name(franchise):
	if franchise == 1:
		return('Matt & Ross')
	elif franchise == 2:
		return('Scott & James')
	elif franchise == 3:
		return('Doug')
	elif franchise == 4:
		return('Crockett')
	elif franchise == 5:
		return('Blake')
	elif franchise == 6:
		return('Kfish')
	elif franchise == 7:
		return('Kyle')
	elif franchise == 8:
		return('Gaudet & Cameron')
	elif franchise == 9:
		return('RTRO')
	elif franchise == 10:
		return('Mitch')
	elif franchise == 11:
		return('Nick & Mickey')
	elif franchise == 12:
		return('Joseph & Mike')

def get_franchise_number(input):
	# These inputs correspond to groupme ids as of 10/12/18
	if input == '3491271' or input == '7435976':
		return(1)
	elif input == '7435971' or input == '3931770' or input == 2:
		return(2)
	elif input == '7435973' or input == 3:
		return(3)
	elif input == '7435977' or input == 4:
		return(4)
	elif input == '12610331' or input == 5:
		return(5)
	elif input == '7435975' or input == 6:
		return(6)
	elif input == '7435974' or input == 7:
		return(7)
	elif input == '22905' or input == 8:
		return(8)
	elif input == '4747679' or input == '29542085' or input == '3054470' or input == '7435972' or input == 9:
		return(9)
	elif input == '7435969' or input == 10:
		return(10)
	elif input == '3165727' or input == '3159027' or input == 11:
		return(11)
	elif input == '6602218' or input == '55209013' or input == 12:
		return(12)

def text_id_franchise(text):
	if re.search('mattjohn', text, re.I) or re.search('matt john', text, re.I) or re.search('gilhop', text, re.I) or re.search('jordan', text, re.I) or re.search('bob', text, re.I) or re.search('rtro', text, re.I) or re.search('retro', text, re.I):
		return(9, 1)
	elif re.search('matt', text, re.I) or re.search('ross', text, re.I) or re.search('butler', text, re.I):
		return(1, 1)
	elif re.search('scott', text, re.I) or re.search('james', text, re.I) or re.search('choice', text, re.I) or re.search('tpc', text, re.I):
		return(2, 1)
	elif re.search('doug', text, re.I) or re.search('rollin', text, re.I):
		return(3, 1)
	elif re.search('crocket', text, re.I) or re.search('taylor', text, re.I):
		return(4, 1)
	elif re.search('blake', text, re.I):
		return(5, 1)
	elif re.search('kfish', text, re.I) or re.search('kmish', text, re.I) or re.search('kevin', text, re.I) or re.search('fischer', text, re.I):
		return(6, 1)
	elif re.search('kyle', text, re.I) or re.search('dttw', text, re.I) or re.search('douille', text, re.I):
		return(7, 1)
	elif re.search('gaudet', text, re.I) or re.search('cameron', text, re.I) or re.search('john', text, re.I) or re.search('zj', text, re.I):
		return(8, 1)
	elif re.search('mitch', text, re.I):
		return(10, 1)
	elif re.search('nick', text, re.I) or re.search('mickey', text, re.I):
		return(11, 1)
	elif re.search('joseph', text, re.I) or re.search('craig', text, re.I) or re.search('mike', text, re.I) or re.search('black', text, re.I) or re.search('trading', text, re.I):
		return(12, 1)
	else: 
		return('none', 2)



def franchise_summary(franchise_number):
	# Pull from db
	franchise_index = franchise_number - 1
	franchise_name_list = ['Matt & Ross', 'Scott & James', 'Doug', 'Crockett', 'Blake', 'Kfish', 'Kyle', 'Gaudet & Cameron', 'Gilhop & MJ', 'Mitch', 'Nick & Mickey', 'Joseph & Mike']
	con = pymysql.connect(host=os.environ['DB_ACCESS_HOST'], user=os.environ['DB_ACCESS_USER'], password=os.environ['DB_ACCESS_PASSWORD'], database=os.environ['DB_ACCESS_DATABASE'])
	cur = con.cursor()
	cur.execute("SELECT * FROM temporary_franchise_summary WHERE franchise=%s;", (franchise_name_list[franchise_index]))
	all_temporary_data = cur.fetchall()[0]
	con.commit()
	cur.execute("SELECT * FROM annual_franchise_summary WHERE franchise=%s;", (franchise_name_list[franchise_index]))
	all_annual_data = cur.fetchall()[0]
	con.commit()
	con.close()

	franchise_name = get_franchise_name(franchise_number)
	champion_message = all_annual_data[1]
	sacko_message = all_annual_data[2]
	ranking_2015 = all_annual_data[3]
	ranking_2016 = all_annual_data[4]
	ranking_2017 = all_annual_data[5]
	average_ranking = all_annual_data[11]
	playoff_appearances = all_annual_data[12]
	best_ppg_season = all_annual_data[13]
	best_ppg_season_year = all_annual_data[14]
	best_record = all_annual_data[15]
	best_record_year = all_annual_data[16]
	rivalry_record = all_annual_data[17]
	avg_draft_pick = all_annual_data[18]

	average_ppg = all_temporary_data[1]
	average_ppg_rank = all_temporary_data[2]
	win_pct = round((all_temporary_data[3] * 100),1)
	win_pct_rank = all_temporary_data[4]
	highest_score = all_temporary_data[5]
	highest_score_year = all_temporary_data[6]
	highest_score_week = all_temporary_data[7]
	largest_margin = all_temporary_data[8]
	largest_margin_year = all_temporary_data[9]
	largest_margin_week = all_temporary_data[10]
	qb_name = all_temporary_data[11]
	qb_points = all_temporary_data[12]
	rb_name = all_temporary_data[13]
	rb_points = all_temporary_data[14]
	wr_name = all_temporary_data[15]
	wr_points = all_temporary_data[16]
	te_name = all_temporary_data[17]
	te_points = all_temporary_data[18]
	dst_name = all_temporary_data[19]
	dst_points = all_temporary_data[20]
	k_name = all_temporary_data[21]
	k_points = all_temporary_data[22]

	divider_stars = '***   ***   ***   ***'
	divider_dashes = '--------------------'
	champion = '*** **  League Champion  ** ***'
	avgrankrow = 'Avg Rank {} | Playoffs {}'.format(average_ranking, playoff_appearances)
	ppgrow = '{} PPG (#{})  ...  {} Win% (#{})'.format(average_ppg, average_ppg_rank, win_pct, win_pct_rank)
	bestperformancesrow = '=== Best Performances ==='

	if champion_message == 'None':
		if sacko_message == 'None':
			message = ">> {} Summary <<\n\n'15   '16   '17  (Modern Era)\n#{}   #{}   #{}\n{:^32}\n{:^32}\n{:^32}\n{:^32}\n\nHighest Score: {}    ({}/{})\nBest Season: {} PPG    ({})\nBest Record: {}    ({})\nLargest Margin: {}    ({}/{})\nRivalry: {}   |   Avg Draft Pick: {}\n\n{:^32}\nQB - {} {}\nRB - {} {}\nWR - {} {}\nTE - {} {}\nD/ST - {} {}\nK - {} {}".format(franchise_name, ranking_2015, ranking_2016, ranking_2017, divider_dashes, avgrankrow, divider_dashes, ppgrow, highest_score, highest_score_year, highest_score_week, best_ppg_season, best_ppg_season_year, best_record, best_record_year, largest_margin, largest_margin_year, largest_margin_week, rivalry_record, avg_draft_pick, bestperformancesrow, qb_name, qb_points, rb_name, rb_points, wr_name, wr_points, te_name, te_points, dst_name, dst_points, k_name, k_points)
		else:
			message = ">> {} Summary <<\n\n### Sacko: {}\n\n'15   '16   '17  (Modern Era)\n#{}   #{}   #{}\n{:^32}\n{:^32}\n{:^32}\n{:^32}\n\nHighest Score: {}    ({}/{})\nBest Season: {} PPG    ({})\nBest Record: {}    ({})\nLargest Margin: {}    ({}/{})\nRivalry: {}   |   Avg Draft Pick: {}\n\n{:^32}\nQB - {} {}\nRB - {} {}\nWR - {} {}\nTE - {} {}\nD/ST - {} {}\nK - {} {}".format(franchise_name, sacko_message, ranking_2015, ranking_2016, ranking_2017, divider_dashes, avgrankrow, divider_dashes, ppgrow, highest_score, highest_score_year, highest_score_week, best_ppg_season, best_ppg_season_year, best_record, best_record_year, largest_margin, largest_margin_year, largest_margin_week, rivalry_record, avg_draft_pick, bestperformancesrow, qb_name, qb_points, rb_name, rb_points, wr_name, wr_points, te_name, te_points, dst_name, dst_points, k_name, k_points)
	else:
		if sacko_message == 'None':
			message = ">> {} Summary <<\n\n{:^32}\n{:^32}\n\n'15   '16   '17  (Modern Era)\n#{}   #{}   #{}\n{:^32}\n{:^32}\n{:^32}\n{:^32}\n\nHighest Score: {}    ({}/{})\nBest Season: {} PPG    ({})\nBest Record: {}    ({})\nLargest Margin: {}    ({}/{})\nRivalry: {}   |   Avg Draft Pick: {}\n\n{:^32}\nQB - {} {}\nRB - {} {}\nWR - {} {}\nTE - {} {}\nD/ST - {} {}\nK - {} {}".format(franchise_name, champion, champion_message, ranking_2015, ranking_2016, ranking_2017, divider_dashes, avgrankrow, divider_dashes, ppgrow, highest_score, highest_score_year, highest_score_week, best_ppg_season, best_ppg_season_year, best_record, best_record_year, largest_margin, largest_margin_year, largest_margin_week, rivalry_record, avg_draft_pick, bestperformancesrow, qb_name, qb_points, rb_name, rb_points, wr_name, wr_points, te_name, te_points, dst_name, dst_points, k_name, k_points)
		else:
			message = ">> {} Summary <<\n\n{:^32}\n{:^32}\n\n### Sacko: {}\n\n'15   '16   '17  (Modern Era)\n#{}   #{}   #{}\n{:^32}\n{:^32}\n{:^32}\n{:^32}\n\nHighest Score: {}    ({}/{})\nBest Season: {} PPG    ({})\nBest Record: {}    ({})\nLargest Margin: {}    ({}/{})\nRivalry: {}   |   Avg Draft Pick: {}\n\n{:^32}\nQB - {} {}\nRB - {} {}\nWR - {} {}\nTE - {} {}\nD/ST - {} {}\nK - {} {}".format(franchise_name, champion, champion_message, sacko_message, ranking_2015, ranking_2016, ranking_2017, divider_dashes, avgrankrow, divider_dashes, ppgrow, highest_score, highest_score_year, highest_score_week, best_ppg_season, best_ppg_season_year, best_record, best_record_year, largest_margin, largest_margin_year, largest_margin_week, rivalry_record, avg_draft_pick, bestperformancesrow, qb_name, qb_points, rb_name, rb_points, wr_name, wr_points, te_name, te_points, dst_name, dst_points, k_name, k_points)  

	# message = 'ok {} << franchise'.format(franchise_number)
	send_message(message)





def sandbox_testing(text):
	# Just don't output 'testing' or 'bot' into the sandbox and you're good
	
	# final_message = 'message on first line\n'
	# for i in range(0,3):
	# 	final_message = final_message + '{:>6}-{:17} proj: {}'.format(score[i],team[i],proj[i]) + '\n'
	# header = 'center'
	# final_message = '{:36}\n'.format(header)
	# final_message = '{:^36}'.format(header)
	# for i in range(0,3):
	# 	final_message = final_message + '{:>6}-{:17} proj: {}'.format(score[i],team[i],proj[i]) + '\n'
	snippet = 'test'
	final_message = '{:<8}{:^8}{:>8}\n{:<8}{:^8}{:>8}\n{:<8}{:^8}{:>8}'.format(snippet,snippet,snippet,snippet,snippet,snippet,snippet,snippet,snippet)
	message_to_sandbox(final_message)
	return('ok',200)

def message_to_sandbox(msg):
	# Sent to File Sharing group for testing purposes
	url = 'https://api.groupme.com/v3/bots/post'
	message = {
		'text': msg,  
		'bot_id': os.environ['SANDBOX_TOKEN'] 
		}
	request = Request(url, urlencode(message).encode())
	json = urlopen(request).read().decode()

	
	# json = requests.post(url, message)
	return('ok',200)


def get_data_no_webdriver(franchise_number, message_type):
	try:
		from bs4 import BeautifulSoup
		from urllib.request import urlopen

		season = 2018
		week = database_access('settings', 'week')

		url = 'http://games.espn.com/ffl/scoreboard?leagueId=133377&matchupPeriodId=%s&seasonId=%s' % (week, season)
		page = urlopen(url)
		page_content = page.read()
		soup = BeautifulSoup(page_content, "lxml")

		# This gives a list of franchise numbers in the order that they're matched up
		franchise_number_list = re.findall(r'(?<=id="teamscrg_)[0-9]*', str(soup)) # confirmed: this creates a list
		points_list = []
		projected_list = []

		# The if statement tests to see if the matchup is ongoing (returns true if so) or already completed (returns false if so)
		if re.search('tmTotalPts_', str(soup)):
			for i in franchise_number_list:
				points_list.append(soup.select_one('#tmTotalPts_%s' % (i)).text)
				projected_list.append(soup.select_one('#team_liveproj_%s' % (i)).text)
		else:
			points_list = re.findall(r'(?<=width="18%">)[0-9]*[.]?[0-9]', str(soup))
			projected_list = 'GAME COMPLETED'
			sys.stdout.write('nestled into a completed game. no projs')
	except:
		send_message('Error. Our combination of free cloud hosting + webdriver is lagging like a noob. Try a different command, or retry the same command in a few mintues.')
		return('get_data_no_webdriver failed')

	########## Put into ClearDb
	con = pymysql.connect(host=os.environ['DB_ACCESS_HOST'], user=os.environ['DB_ACCESS_USER'], password=os.environ['DB_ACCESS_PASSWORD'], database=os.environ['DB_ACCESS_DATABASE'])
	cur = con.cursor()

	cur.execute("DROP TABLE temporary_scraped_matchups;")
	con.commit()
	cur.execute("CREATE TABLE temporary_scraped_matchups (game INT, franchise INT, points DECIMAL(4,1), projected DECIMAL(4,1), PRIMARY KEY(game));")
	con.commit()

	if projected_list != 'GAME COMPLETED':
		for i in range(len(franchise_number_list)):  # range(0,12)
			cur.execute("INSERT INTO  temporary_scraped_matchups VALUES(%s, %s, %s, %s);", (i, franchise_number_list[i], points_list[i], projected_list[i]))
			con.commit()
	else:
		for i in range(len(franchise_number_list)):   # range(0,12)
			cur.execute("INSERT INTO temporary_scraped_matchups VALUES(%s, %s, %s, 999.9);", (i, franchise_number_list[i], points_list[i]))
			con.commit()

	con.close()

	if projected_list == 'GAME COMPLETED':
		games_over = 'yes'
	else:
		games_over = 'no'

	#### Make sure to get rid of this artifact when refactoring into proper modules
	standings = 2

	length_of_data = len(franchise_number_list)

	if standings == 1:
		get_standings()
		return('ok',200)
	else:
		get_games_from_temp_cleardb(franchise_number, message_type, games_over, length_of_data)
		return('ok',200)



def get_games_from_temp_cleardb(franchise_number, message_type, games_over, length_of_data):
	########## Get from ClearDb
	con = pymysql.connect(host=os.environ['DB_ACCESS_HOST'], user=os.environ['DB_ACCESS_USER'], password=os.environ['DB_ACCESS_PASSWORD'], database=os.environ['DB_ACCESS_DATABASE'])
	cur = con.cursor()

	###### Get single score
	if message_type == 1:
		cur.execute("SELECT game, franchise, points, projected FROM temporary_scraped_matchups WHERE franchise=%s", (franchise_number))
		franchise_data = cur.fetchall()[0]
		con.commit()
		game_number = franchise_data[0]

		if game_number % 2 == 0:
			opponent_game = game_number + 1
			# sys.stdout.write('even index')
		else: 
			opponent_game = game_number - 1
			# sys.stdout.write('odd index')

		cur.execute("SELECT game, franchise, points, projected FROM temporary_scraped_matchups WHERE game=%s", (opponent_game))
		opponent_data = cur.fetchall()[0]
		con.commit()

		con.close()

		create_game_data_message_single(franchise_data, opponent_data, games_over)
		return('ok',200)

		########################### This weekend: within the games_over if's, split again. if week < 14: what you have now  ... elif week == 14: split for into === Playoffs === for i in range(0, 4) and === Consolation Ladder === for i in range(4, length_of_whatver) ...  elif week == 15: split for into === Playoffs === for i in range(0, 4) and === Consolation Ladder === for i in range(6, length_of_whatver) .....  if week == 16: for i in range(0,2): =====\n === League Championship === .. for i in range(yaddayadda) === 3rd Place Game .. 5th Place Game  Consolation Ladder Championship .. 9th Place Game .. Sacko Game
	######### For whole scoreboard
	elif message_type == 2:
		if games_over == 'yes':
			week = database_access('settings', 'week')
			final_scoreboard = '*** Week %i Final Scoreboard ***\n' % week
			for i in range(length_of_data)[::2]:  # range(0,12)
				cur.execute("SELECT game, franchise, points, projected FROM temporary_scraped_matchups WHERE game=%s;", (i))
				first_line_raw = cur.fetchall()[0]
				con.commit()
				cur.execute("SELECT game, franchise, points, projected FROM temporary_scraped_matchups WHERE game=%s;", (i+1))
				second_line_raw = cur.fetchall()[0]
				con.commit()
				final_scoreboard = final_scoreboard + '{} - {}\n{} - {}\n===== ===== =====\n'.format(first_line_raw[2], get_franchise_name(first_line_raw[1]), second_line_raw[2], get_franchise_name(second_line_raw[1]))
			
			con.close()
			send_message(final_scoreboard)
			return('ok',200)
		
		elif games_over == 'no':
			week = database_access('settings', 'week')
			live_scoreboard = '*** Week %i Live Scoreboard ***\n' % week
			for i in range(length_of_data)[::2]:   # range(0,12)
				cur.execute("SELECT game, franchise, points, projected FROM temporary_scraped_matchups WHERE game=%s;", (i))
				first_line_raw = cur.fetchall()[0]
				con.commit()
				cur.execute("SELECT game, franchise, points, projected FROM temporary_scraped_matchups WHERE game=%s;", (i+1))
				second_line_raw = cur.fetchall()[0]
				con.commit()
				live_scoreboard = live_scoreboard + '{} - {} | proj: {}\n{} - {} | proj: {}\n===== ===== =====\n'.format(first_line_raw[2], get_franchise_name(first_line_raw[1]), first_line_raw[3], second_line_raw[2], get_franchise_name(second_line_raw[1]), second_line_raw[3])
			
			con.close()
			send_message(live_scoreboard)
			return('ok',200)

def create_game_data_message_single(franchise, opponent, games_over):
	if games_over == 'yes':
		first_line = '{} - {}'.format(franchise[2], get_franchise_name(franchise[1]))
		second_line = '{} - {}'.format(opponent[2], get_franchise_name(opponent[1]))
		single_game_final_score = '{}\n{}'.format(first_line, second_line)
		send_message(single_game_final_score)
		return('ok',200)
		# WORKED B
	else:
		first_line = '{} - {}'.format(franchise[2], get_franchise_name(franchise[1]))
		second_line = '{} - {}'.format(opponent[2], get_franchise_name(opponent[1]))
		single_game_ongoing_score = '{} | proj: {}\n{} | proj: {}'.format(first_line, franchise[3], second_line, opponent[3])
		send_message(single_game_ongoing_score)
		return('ok',200)
		# WORKED C



def get_standings():
	# When refactoring all of the code, be sure to put an if statement in so that anything in week 1 gives a message 'No games played yet', and 'N/A' for playoff weeks
	try:
		from bs4 import BeautifulSoup
		from urllib.request import urlopen

		season = 2018
		week = database_access('settings', 'week')

		url = 'http://games.espn.com/ffl/scoreboard?leagueId=133377&matchupPeriodId=%s&seasonId=%s' % (week, season)
		page = urlopen(url)
		page_content = page.read()
		soup = BeautifulSoup(page_content, "lxml")

		# This gives a list of franchise numbers in the order that they're matched up
		franchise_number_list = re.findall(r'(?<=id="teamscrg_)[0-9]*', str(soup)) # confirmed: this creates a list
		points_list = []
		projected_list = []

		# The if statement tests to see if the matchup is ongoing (returns true if so) or already completed (returns false if so)
		if re.search('tmTotalPts_', str(soup)):
			for i in franchise_number_list:
				points_list.append(soup.select_one('#tmTotalPts_%s' % (i)).text)
				projected_list.append(soup.select_one('#team_liveproj_%s' % (i)).text)
		else:
			points_list = re.findall(r'(?<=width="18%">)[0-9]*[.]?[0-9]', str(soup))
			projected_list = 'GAME COMPLETED'
			sys.stdout.write('nestled into a completed game. no projs')
	except:
		# send_message('Error. Our combination of free cloud hosting + webdriver is lagging like a noob. Try a different command, or retry the same command in a few mintues.')
		return('get_data_no_webdriver failed')

	########## Put into ClearDb
	con = pymysql.connect(host=os.environ['DB_ACCESS_HOST'], user=os.environ['DB_ACCESS_USER'], password=os.environ['DB_ACCESS_PASSWORD'], database=os.environ['DB_ACCESS_DATABASE'])
	cur = con.cursor()

	cur.execute("DROP TABLE temporary_scraped_matchups;")
	con.commit()
	cur.execute("CREATE TABLE temporary_scraped_matchups (game INT, franchise INT, points DECIMAL(4,1), projected DECIMAL(4,1), PRIMARY KEY(game));")
	con.commit()

	if projected_list != 'GAME COMPLETED':
		for i in range(0,12):
			cur.execute("INSERT INTO  temporary_scraped_matchups VALUES(%s, %s, %s, %s);", (i, franchise_number_list[i], points_list[i], projected_list[i]))
			con.commit()
	else:
		for i in range(0,12):
			cur.execute("INSERT INTO temporary_scraped_matchups VALUES(%s, %s, %s, 999.9);", (i, franchise_number_list[i], points_list[i]))
			con.commit()

	con.close()

	get_standings_2()
	return('ok',200)

def get_standings_2():
	import pymysql

	def result_generator(a_score, b_score):
	    if a_score > b_score:
	        return('W', 'L')
	    elif a_score < b_score:
	        return('L', 'W')
	    else:
	        return('T', 'T')


	con = pymysql.connect(host=os.environ['DB_ACCESS_HOST'], user=os.environ['DB_ACCESS_USER'], password=os.environ['DB_ACCESS_PASSWORD'], database=os.environ['DB_ACCESS_DATABASE'])
	cur = con.cursor()

	cur.execute("DROP TABLE temporary_intermediate_standings;")
	con.commit()
	cur.execute("CREATE TABLE temporary_intermediate_standings (franchise INT, intermediate_points DECIMAL(4,1), intermediate_result VARCHAR(10), PRIMARY KEY(franchise));")
	con.commit()

	cur.execute("DROP TABLE temporary_live_standings;")
	con.commit()
	cur.execute("CREATE TABLE temporary_live_standings (franchise INT, live_win_pct DECIMAL(6,5), live_points DECIMAL(5,1), live_wins INT, live_losses INT, live_ties INT, PRIMARY KEY(franchise));")
	con.commit()
	con.close()
	#   data[0][0] == wins  ; data[0][1] == losses  data[0][2] == ties   data[0][3] == sum_points

	for game in range(0,12,2):
	    con = pymysql.connect(host=os.environ['DB_ACCESS_HOST'], user=os.environ['DB_ACCESS_USER'], password=os.environ['DB_ACCESS_PASSWORD'], database=os.environ['DB_ACCESS_DATABASE'])
	    cur = con.cursor()
	    cur.execute("SELECT franchise, points FROM temporary_scraped_matchups WHERE game=%s;", (game))
	    team_a_tuple = cur.fetchall()[0]
	    con.commit()
	    team_a_franchise = team_a_tuple[0]
	    team_a_score = team_a_tuple[1]
	    cur.execute("SELECT franchise, points FROM temporary_scraped_matchups WHERE game=%s;", (game+1))
	    team_b_tuple = cur.fetchall()[0]
	    con.commit()

	    team_b_franchise = team_b_tuple[0]
	    team_b_score = team_b_tuple[1]
	    a_result, b_result = result_generator(team_a_score, team_b_score)
	    
	    cur.execute("INSERT INTO temporary_intermediate_standings (franchise, intermediate_points, intermediate_result) VALUES (%s, %s, %s);", (team_a_franchise, team_a_score, a_result))
	    con.commit()
	    cur.execute("INSERT INTO temporary_intermediate_standings (franchise, intermediate_points, intermediate_result) VALUES (%s, %s, %s);", (team_b_franchise, team_b_score, b_result))
	    con.commit()
	    con.close()
	    

	for franchise in range(1,13):
	    con = pymysql.connect(host=os.environ['DB_ACCESS_HOST'], user=os.environ['DB_ACCESS_USER'], password=os.environ['DB_ACCESS_PASSWORD'], database=os.environ['DB_ACCESS_DATABASE'])
	    cur = con.cursor()
	    cur.execute("SELECT intermediate_points, intermediate_result FROM temporary_intermediate_standings WHERE franchise=%s;", (franchise))
	    data_tuple = cur.fetchall()[0]
	    con.commit()
	    
	    intermediate_points = data_tuple[0]
	    intermediate_result = data_tuple[1]
	    
	    cur.execute("SELECT wins, losses, ties, sum_points FROM temporary_scrape_standings WHERE franchise=%s;", (franchise))
	    weekly_scrape_tuple = cur.fetchall()[0]
	    con.commit()
	    
	    old_wins = weekly_scrape_tuple[0]
	    old_losses = weekly_scrape_tuple[1]
	    old_ties = weekly_scrape_tuple[2]
	    old_sum_points = weekly_scrape_tuple[3]
	    
	    if intermediate_result == 'W':
	        wins = old_wins + 1
	        losses = old_losses
	        ties = old_ties
	    elif intermediate_result == 'L':
	        wins = old_wins
	        losses = old_losses + 1
	        ties = old_ties
	    else:
	        wins = old_wins
	        losses = old_losses
	        ties = old_ties + 1
	    
	    live_win_pct = (wins + (ties * 0.5)) / (wins + losses + ties)
	    live_points = old_sum_points + intermediate_points
	    
	    cur.execute("INSERT INTO temporary_live_standings (franchise, live_win_pct, live_points, live_wins, live_losses, live_ties) VALUES (%s, %s, %s, %s, %s, %s);", (franchise, "%.5f"%live_win_pct, live_points, wins, losses, ties))
	    con.commit()
	    
	    
	    cur.execute("SELECT franchise, live_wins, live_losses, live_ties, live_points FROM temporary_live_standings ORDER BY live_win_pct, live_points;")
	    standings_tuple = cur.fetchall()
	    con.commit()
	    
	    con.close()
	    
	rankings_headers = [12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
	live_standings = '*** Live Standings - based on current live scores ***\n\n'
	for i in range(11,-1,-1):
		live_standings = live_standings + '{}. {} {}-{}-{} pts: {}\n'.format(rankings_headers[i], get_franchise_name(standings_tuple[i][0]), standings_tuple[i][1], standings_tuple[i][2], standings_tuple[i][3], standings_tuple[i][4])
		
		if i == 10:
			live_standings = live_standings + '----- Top 2 = Byes -----\n'
		if i == 6:
			live_standings = live_standings + '=====  Playoff cut line  =====\n'

	send_message(live_standings)
	return('ok',200)



	    # craft_standings_message(standings_tuple)
	    # return('ok',200)
		#con.close()
		# number 1 team == 11  ... down to number 12 team being index 0
		#print(standings_tuple[11][0]) == franchise number
		# [1] == wins
		# [2] == losses
		# [3] == ties

# def craft_standings_message(standings_tuple):
	# live_standings = '*** Current Live Standings ***\n'
	# for i in range(11,-1,-1):
	# 	live_standings = live_standings + '{} {}-{}-{}\n'.format(get_franchise_name(standings_tuple[i][0]), standings_tuple[i][1], standings_tuple[i][2], standings_tuple[i][3])
		
	# 	if i == 6:
	# 		live_standings = live_standings + '===============\n'

	# send_message(live_standings)
	# return('ok',200)







if __name__ == '__main__':
	app.run()

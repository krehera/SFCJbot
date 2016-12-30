from sys import argv
import challonge
import string
import twitter
import random

# This script needs three files and a datetime as arguments to run.
# The first file must be a newline-delimited list of the games which you wish to run tournaments for.
# The first file should not have a newline after the last game.
# The second file should be two lines, containing your Challonge username and API key.
# The third file should be four lines, countaining your Twitter authentication information.
# datetime_tourny_start format: "2015-01-19T16:57:17-05:00"
# you can get this agument with gnu's date via a command similar to 'date -d "next Friday 8 pm" +%FT%H:%M:%S%:z'
this_program, games_filename, challonge_auth_filename, twitter_auth_filename, datetime_tourny_start = argv

# read the games file
file_of_games = open(games_filename)
games = file_of_games.readlines()
file_of_games.close()

# read in Challonge auth info
challonge_auth_file = open(challonge_auth_filename)
challonge_username = challonge_auth_file.readline().rstrip()
challonge_key = challonge_auth_file.readline().rstrip()
challonge_auth_file.close()
challonge.set_credentials(challonge_username, challonge_key)

# read in Twitter auth info
twitter_auth_file = open(twitter_auth_filename)
twitter_consumer_key = twitter_auth_file.readline()
twitter_consumer_secret = twitter_auth_file.readline()
twitter_access_token = twitter_auth_file.readline()
twitter_access_secret = twitter_auth_file.readline()
twitter_auth_file.close()
twitter_api = twitter.Api(consumer_key=twitter_consumer_key, consumer_secret=twitter_consumer_secret, access_token_key=twitter_access_token, access_token_secret=twitter_access_secret)

# get the game listed at the top of the file. remove it from the start of the list and add it to the end.
# this readies the file to be read again next week, with the next game now at the top of the file and the current game now at the end
game_to_make_a_tournament_for = games[0]
#print("game: "+game_to_make_a_tournament_for)
games = games[1:]
games.append(game_to_make_a_tournament_for)

# create a tournament for the game
tourny_url = "".join(random.choice(string.ascii_lowercase) for _ in xrange(0, 15))
tournament = {'tournament_type':"double elimination", 'game_name':game_to_make_a_tournament_for, 'open_signup':True, 'start_at':datetime_tourny_start}
response = challonge.tournaments.create(game_to_make_a_tournament_for, tourny_url, **tournament) 
#print("response: " + str(response))

# write the file
file_of_games = open(games_filename, "w")
for line in games:
	file_of_games.write(line)
file_of_games.close()

# TODO tweet about it


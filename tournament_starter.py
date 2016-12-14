from sys import argv
import challonge
from datetime import date

this_program, challonge_auth_filename = argv

challonge_auth_file = open(challonge_auth_filename)
challonge_username = challonge_auth_file.readline().rstrip()
challonge_key = challonge_auth_file.readline().rstrip()
challonge_auth_file.close()
challonge.set_credentials(challonge_username, challonge_key)

today = str(date.today().isoformat())

tournaments = challonge.tournaments.index(state="pending")
for tournament in tournaments:
	if str(tournament["start-at"])[:10] == today:
		challonge.tournaments.start(tournament["id"])



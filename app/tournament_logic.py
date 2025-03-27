from app.models import db, Tournament, Team, Match

def update_tournament_standings(tournament_id):
    tournament = Tournament.query.get(tournament_id)
    if not tournament:
        return
    
    standings = {team.id: {'team': team, 'points': 0, 'games_played': 0, 'wins': 0, 'draws': 0, 'losses': 0} for team in tournament.teams}
    
    completed_matches = Match.query.filter_by(tournament_id=tournament_id, status='Completed').all()
    
    for match in completed_matches:
        standings[match.team1_id]['games_played'] += 1
        standings[match.team2_id]['games_played'] += 1
        
        if match.team1_score > match.team2_score:
            standings[match.team1_id]['points'] += 3
            standings[match.team1_id]['wins'] += 1
            standings[match.team2_id]['losses'] += 1
        elif match.team1_score < match.team2_score:
            standings[match.team2_id]['points'] += 3
            standings[match.team2_id]['wins'] += 1
            standings[match.team1_id]['losses'] += 1
        else:
            standings[match.team1_id]['points'] += 1
            standings[match.team2_id]['points'] += 1
            standings[match.team1_id]['draws'] += 1
            standings[match.team2_id]['draws'] += 1
    
    # Aktualisiere die Teamstatistiken in der Datenbank
    for team_stats in standings.values():
        team = team_stats['team']
        team.points = team_stats['points']
        team.games_played = team_stats['games_played']
        team.wins = team_stats['wins']
        team.draws = team_stats['draws']
        team.losses = team_stats['losses']
    
    db.session.commit()


def generate_round_robin_schedule(teams):
    if len(teams) % 2 != 0:
        teams.append("Bye")  # Füge ein Freilos hinzu, wenn die Anzahl der Teams ungerade ist

    schedule = []
    num_rounds = len(teams) - 1
    num_matches_per_round = len(teams) // 2

    for round_num in range(num_rounds):
        round_matches = []
        for match_num in range(num_matches_per_round):
            home = teams[match_num]
            away = teams[-(match_num + 1)]
            round_matches.append((home, away))
        schedule.append(round_matches)
        teams.insert(1, teams.pop())  # Rotiere die Teams

    return schedule

def generate_knockout_matches(teams):
    if len(teams) % 2 != 0:
        raise ValueError("Die Anzahl der Teams muss gerade sein, um ein Knockout-Turnier zu erstellen.")

    matches = []
    round_number = 1

    while len(teams) > 1:
        round_matches = []
        for i in range(0, len(teams), 2):
            match = {
                'round': round_number,
                'team1': teams[i],
                'team2': teams[i + 1]
            }
            round_matches.append(match)
        matches.append(round_matches)

        # Gewinner der aktuellen Runde simulieren (z.B. Team1 gewinnt immer)
        teams = [match['team1'] for match in round_matches]
        round_number += 1

    return matches


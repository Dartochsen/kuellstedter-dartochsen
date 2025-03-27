from celery import shared_task
from flask import current_app
from app.extensions import celery, db, cache
from app.models.player import Player
from app.models.game import Game
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta
import logging
import time

logger = get_task_logger(__name__)

class TaskFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, 'task_id'):
            record.task_id = record.task_id or '???'
        if hasattr(record, 'task_name'):
            record.task_name = record.task_name or '???'
        return super().format(record)

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 5})
def example_task(self, x, y):
    logger.info(f"Starte example_task mit Parametern: x={x}, y={y}")
    try:
        result = x + y
        logger.info(f"example_task erfolgreich abgeschlossen. Ergebnis: {result}")
        return result
    except Exception as e:
        logger.error(f"Fehler in example_task: {str(e)}")
        raise

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 5})
def long_running_task(self):
    logger.info("Starte long_running_task")
    try:
        # Ihre bestehende Implementierung hier
        logger.info("long_running_task erfolgreich abgeschlossen")
        return "Task abgeschlossen"
    except Exception as e:
        logger.error(f"Fehler in long_running_task: {str(e)}")
        raise

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 5})
def send_email(self, recipient, subject, body):
    logger.info(f"Starte send_email an: {recipient}")
    try:
        # Ihre bestehende Implementierung hier
        logger.info(f"E-Mail erfolgreich gesendet an: {recipient}")
        return f"E-Mail an {recipient} gesendet"
    except Exception as e:
        logger.error(f"Fehler beim Senden der E-Mail an {recipient}: {str(e)}")
        raise

@celery.task
def generate_player_analysis(player_id):
    from app import create_app
    with create_app().app_context():
        from app.analysis.player_analysis import analyze_player_trend, generate_training_recommendation
        trend = analyze_player_trend(player_id)
        recommendation = generate_training_recommendation(player_id)
        # Hier könnten Sie die Ergebnisse in der Datenbank speichern oder eine Benachrichtigung senden
        # Invalidate relevant caches
        cache.delete(f'player_analysis_{player_id}')
        return {"trend": trend, "recommendation": recommendation}

@celery.task(name='analyze_player_data_task')
def analyze_player_data_task(player_id):
    from app import create_app
    with create_app().app_context():
        from app.models import Player
        player = Player.query.get(player_id)
        if player:
            # Hier führen Sie Ihre Analyse durch
            average_score = player.calculate_average_score()
            games_played = player.games_played
            win_rate = player.calculate_win_rate()
            
            # Simulieren Sie eine zeitaufwändige Aufgabe
            time.sleep(5)
            
            # Invalidate relevant caches
            cache.delete(f'player_analysis_{player_id}')
            
            return {
                "player_id": player_id,
                "average_score": average_score,
                "games_played": games_played,
                "win_rate": win_rate
            }
        return f"Could not analyze data for player {player_id}"

@celery.task
def test_task(x, y):
    logger.info(f'Addiere {x} und {y}')
    return x + y

@celery.task(bind=True)
def update_player_statistics(self, player_id):
    logger.info(f"Aktualisiere Statistiken für Spieler {player_id}")
    try:
        player = Player.query.get(player_id)
        if not player:
            logger.error(f"Spieler mit ID {player_id} nicht gefunden")
            return

        # Berechne Statistiken
        games = Game.query.filter((Game.player1_id == player_id) | (Game.player2_id == player_id)).all()
        total_games = len(games)
        wins = sum(1 for game in games if game.winner_id == player_id)
        
        player.games_played = total_games
        player.wins = wins
        player.win_rate = (wins / total_games) * 100 if total_games > 0 else 0
        
        db.session.commit()
        logger.info(f"Statistiken für Spieler {player_id} erfolgreich aktualisiert")
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Statistiken für Spieler {player_id}: {str(e)}")
        raise

@celery.task(bind=True)
def generate_weekly_report(self):
    logger.info("Generiere wöchentlichen Bericht")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        new_players = Player.query.filter(Player.join_date >= start_date).count()
        total_games = Game.query.filter(Game.date >= start_date).count()
        
        # Hier könnten Sie weitere Statistiken berechnen

        report = f"Wöchentlicher Bericht vom {start_date.date()} bis {end_date.date()}:\n"
        report += f"Neue Spieler: {new_players}\n"
        report += f"Gespielte Spiele: {total_games}\n"
        
        logger.info("Wöchentlicher Bericht erfolgreich generiert")
        return report
    except Exception as e:
        logger.error(f"Fehler beim Generieren des wöchentlichen Berichts: {str(e)}")
        raise

@celery.task(bind=True)
def clean_old_data(self):
    logger.info("Beginne mit der Bereinigung alter Daten")
    try:
        thirty_days_ago = datetime.now() - timedelta(days=30)
        old_games = Game.query.filter(Game.date < thirty_days_ago).delete()
        db.session.commit()
        logger.info(f"{old_games} alte Spiele wurden gelöscht")
    except Exception as e:
        logger.error(f"Fehler bei der Bereinigung alter Daten: {str(e)}")
        raise
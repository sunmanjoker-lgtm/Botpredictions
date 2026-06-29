import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict

TOKEN = '8917243606:AAHojdm5VMfKCasorA05zVtVphYXyNb4n5k'
CHAT_ID = 328619258

def send_telegram_message(text: str, parse_mode: str = 'HTML') -> bool:
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    params = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': parse_mode}
    try:
        response = requests.post(url, json=params, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False

def split_message(text: str, max_len: int = 4000) -> List[str]:
    return [text[i:i+max_len] for i in range(0, len(text), max_len)]

# ======= 1. ПРОГНОЗЫ С API-FOOTBALL (БЕСПЛАТНО) =======
def get_football_predictions():
    """Получает прогнозы с бесплатного API"""
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": "361831563ad048fb88a38be896b4aa93"}
    params = {"dateFrom": datetime.now().strftime('%Y-%m-%d'), "status": "SCHEDULED"}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            matches = []
            for match in data.get('matches', [])[:10]:
                matches.append({
                    'home': match['homeTeam']['name'],
                    'away': match['awayTeam']['name'],
                    'league': match['competition']['name'],
                    'date': match['utcDate'][:10],
                    'time': match['utcDate'][11:16]
                })
            return matches
        return []
    except Exception as e:
        print(f"Ошибка футбол: {e}")
        return []

# ======= 2. ПРОГНОЗЫ С ESPN (БАСКЕТБОЛ) =======
def get_basketball_predictions():
    """Получает матчи NBA с ESPN"""
    today = datetime.now().strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            matches = []
            for event in data.get('events', [])[:10]:
                status = event.get('status', {}).get('type', {}).get('state', '')
                if status == 'final':
                    continue
                comp = event.get('competitions', [{}])[0]
                competitors = comp.get('competitors', [])
                if len(competitors) < 2:
                    continue
                matches.append({
                    'home': competitors[0]['team']['displayName'],
                    'away': competitors[1]['team']['displayName'],
                    'league': 'NBA',
                    'date': today,
                    'time': event.get('date', '')[:16]
                })
            return matches
        return []
    except Exception as e:
        print(f"Ошибка NBA: {e}")
        return []

# ======= 3. ПРОГНОЗЫ С ESPN (БЕЙСБОЛ) =======
def get_mlb_predictions():
    """Получает матчи MLB с ESPN"""
    today = datetime.now().strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={today}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            matches = []
            for event in data.get('events', [])[:10]:
                status = event.get('status', {}).get('type', {}).get('state', '')
                if status == 'final':
                    continue
                comp = event.get('competitions', [{}])[0]
                competitors = comp.get('competitors', [])
                if len(competitors) < 2:
                    continue
                matches.append({
                    'home': competitors[0]['team']['displayName'],
                    'away': competitors[1]['team']['displayName'],
                    'league': 'MLB',
                    'date': today,
                    'time': event.get('date', '')[:16]
                })
            return matches
        return []
    except Exception as e:
        print(f"Ошибка MLB: {e}")
        return []

# ======= 4. ПРОГНОЗЫ С ESPN (ХОККЕЙ) =======
def get_nhl_predictions():
    """Получает матчи NHL с ESPN"""
    today = datetime.now().strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates={today}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            matches = []
            for event in data.get('events', [])[:10]:
                status = event.get('status', {}).get('type', {}).get('state', '')
                if status == 'final':
                    continue
                comp = event.get('competitions', [{}])[0]
                competitors = comp.get('competitors', [])
                if len(competitors) < 2:
                    continue
                matches.append({
                    'home': competitors[0]['team']['displayName'],
                    'away': competitors[1]['team']['displayName'],
                    'league': 'NHL',
                    'date': today,
                    'time': event.get('date', '')[:16]
                })
            return matches
        return []
    except Exception as e:
        print(f"Ошибка NHL: {e}")
        return []

# ======= 5. ОСНОВНАЯ ЛОГИКА =======
def main():
    print("🔍 Сбор матчей на сегодня...")
    
    all_matches = []
    
    # Собираем матчи со всех источников
    football = get_football_predictions()
    nba = get_basketball_predictions()
    mlb = get_mlb_predictions()
    nhl = get_nhl_predictions()
    
    all_matches.extend([('⚽ Футбол', m) for m in football])
    all_matches.extend([('🏀 NBA', m) for m in nba])
    all_matches.extend([('⚾ MLB', m) for m in mlb])
    all_matches.extend([('🏒 NHL', m) for m in nhl])
    
    if not all_matches:
        send_telegram_message("📭 На сегодня матчей не найдено.")
        return
    
    # Формируем сообщение
    lines = []
    lines.append("🏛️ <b>СПОРТИВНЫЕ ПРОГНОЗЫ</b>")
    lines.append(f"📅 {datetime.now().strftime('%d.%m.%Y')}")
    lines.append("=" * 30)
    lines.append("")
    
    for sport, match in all_matches:
        lines.append(f"{sport}")
        lines.append(f"📋 {match['home']} vs {match['away']}")
        lines.append(f"🏆 {match['league']}")
        if match.get('time'):
            lines.append(f"⏰ {match['time']}")
        lines.append("")
    
    # Отправляем
    full_text = "\n".join(lines)
    for part in split_message(full_text):
        send_telegram_message(part)
    
    print("✅ Прогнозы отправлены")

if __name__ == "__main__":
    main()

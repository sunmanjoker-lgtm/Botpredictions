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

# ======= 1. ПОЛУЧЕНИЕ СТАТИСТИКИ КОМАНДЫ =======
def get_team_stats(team_abbr):
    """Получает статистику команды за сезон с ESPN"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/{team_abbr}/statistics"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        data = response.json()
        stats = {}
        for stat in data.get('statistics', []):
            stats[stat.get('name')] = stat.get('value')
        return stats
    except:
        return None

# ======= 2. ПОЛУЧЕНИЕ МАТЧЕЙ MLB =======
def get_mlb_matches():
    """Получает матчи MLB на сегодня и завтра с ESPN"""
    today = datetime.now().strftime('%Y%m%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')
    all_matches = []
    
    for date_str in [today, tomorrow]:
        url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={date_str}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                continue
            data = response.json()
            for event in data.get('events', []):
                status = event.get('status', {}).get('type', {}).get('state', '')
                if status == 'final' or status == 'postponed':
                    continue
                comp = event.get('competitions', [{}])[0]
                competitors = comp.get('competitors', [])
                if len(competitors) < 2:
                    continue
                
                home = competitors[0]['team']
                away = competitors[1]['team']
                start_date = event.get('date')
                
                # Получаем статистику команд
                home_stats = get_team_stats(home['abbreviation'])
                away_stats = get_team_stats(away['abbreviation'])
                
                match = {
                    'home': home['displayName'],
                    'away': away['displayName'],
                    'home_abbr': home['abbreviation'],
                    'away_abbr': away['abbreviation'],
                    'date': date_str,
                    'time': start_date[11:16] if start_date else 'TBD',
                    'home_stats': home_stats,
                    'away_stats': away_stats
                }
                all_matches.append(match)
        except Exception as e:
            print(f"Ошибка ESPN: {e}")
    
    return all_matches

# ======= 3. ПРОГНОЗ =======
def make_prediction(match):
    """Делает прогноз на основе статистики команд"""
    home_stats = match.get('home_stats', {})
    away_stats = match.get('away_stats', {})
    
    home_win_pct = home_stats.get('winPercent', 0.500)
    away_win_pct = away_stats.get('winPercent', 0.500)
    home_era = home_stats.get('era', 4.00)
    away_era = away_stats.get('era', 4.00)
    home_avg = home_stats.get('avg', 0.250)
    away_avg = away_stats.get('avg', 0.250)
    
    # Считаем силу команды
    home_strength = (home_win_pct * 0.4) + (1 - (home_era / 5) * 0.3) + (home_avg * 0.3)
    away_strength = (away_win_pct * 0.4) + (1 - (away_era / 5) * 0.3) + (away_avg * 0.3)
    
    # Домашнее преимущество (+5%)
    prob_home = home_strength / (home_strength + away_strength) + 0.05
    prob_home = max(0.30, min(0.70, prob_home))
    
    if prob_home > 0.55:
        prediction = 'ставка на хозяев'
        confidence = 'высокая' if prob_home > 0.62 else 'средняя'
    elif prob_home < 0.45:
        prediction = 'ставка на гостей'
        confidence = 'высокая' if prob_home < 0.38 else 'средняя'
    else:
        prediction = 'пропустить'
        confidence = 'низкая'
    
    return {
        'prediction': prediction,
        'probability': prob_home,
        'confidence': confidence,
        'home_win_pct': home_win_pct,
        'away_win_pct': away_win_pct,
        'home_era': home_era,
        'away_era': away_era,
        'home_avg': home_avg,
        'away_avg': away_avg
    }

# ======= 4. ФОРМАТИРОВАНИЕ =======
def format_match(match, pred):
    """Форматирует матч с прогнозом"""
    conf_emoji = {
        'высокая': '🟢',
        'средняя': '🟡',
        'низкая': '🔴'
    }.get(pred['confidence'], '⚪')
    
    lines = []
    lines.append(f"⚾ {match['home']} vs {match['away']}")
    lines.append(f"📅 {match['date']} ⏰ {match['time']}")
    lines.append(f"📊 <b>Прогноз:</b> {pred['prediction']} ({pred['probability']:.0%})")
    lines.append(f"🎯 <b>Уверенность:</b> {conf_emoji} {pred['confidence']}")
    lines.append(f"📈 <b>Статистика:</b> {match['home']} {pred['home_win_pct']:.1%} vs {pred['away_win_pct']:.1%} {match['away']}")
    lines.append("")
    return "\n".join(lines)

# ======= 5. ОСНОВНАЯ ЛОГИКА =======
def main():
    print("🔍 Поиск матчей MLB...")
    matches = get_mlb_matches()
    
    if not matches:
        send_telegram_message("⚾ На сегодня матчей MLB не найдено.")
        return
    
    lines = []
    lines.append("⚾ <b>ПРОГНОЗЫ MLB</b>")
    lines.append(f"📅 {datetime.now().strftime('%d.%m.%Y')}")
    lines.append("=" * 30)
    lines.append("")
    
    for match in matches:
        pred = make_prediction(match)
        lines.append(format_match(match, pred))
    
    full_text = "\n".join(lines)
    for part in split_message(full_text):
        send_telegram_message(part)
    
    print(f"✅ Отправлено {len(matches)} прогнозов")

if __name__ == "__main__":
    main()

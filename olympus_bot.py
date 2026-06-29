import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict

TOKEN = '8917243606:AAHojdm5VMfKCasorA05zVtVphYXyNb4n5k'
CHAT_ID = 328619258

def send_telegram_message(text: str, parse_mode: str = 'HTML') -> bool:
    """Отправляет сообщение в Telegram"""
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    params = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': parse_mode}
    try:
        response = requests.post(url, json=params, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False

def split_message(text: str, max_len: int = 4000) -> List[str]:
    """Разбивает длинное сообщение на части"""
    return [text[i:i+max_len] for i in range(0, len(text), max_len)]

def get_olympus_projections() -> Dict:
    """Получает прогнозы с сервера Olympus Bets"""
    try:
        response = requests.get('https://app.olympus-bets.com/api/todays-projections', timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': f'Ошибка {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}

def get_olympus_track_record() -> str:
    """Получает историю результатов"""
    try:
        response = requests.get('https://app.olympus-bets.com/track_record.csv', timeout=15)
        if response.status_code == 200:
            return response.text
        else:
            return "История недоступна"
    except Exception as e:
        return f"Ошибка: {e}"

def format_projection(proj: Dict, sport: str) -> str:
    """Форматирует один прогноз"""
    lines = []
    lines.append(f"🏆 <b>{sport.upper()}</b>")
    lines.append(f"📋 {proj.get('home_team', '')} vs {proj.get('away_team', '')}")
    
    edge = proj.get('edge', 0)
    prob = proj.get('probability', 0)
    ev = proj.get('ev', 0)
    kelly = proj.get('kelly_stake', 0)
    confidence = proj.get('confidence', 'Низкая')
    
    # Определяем эмодзи для уверенности
    conf_emoji = {
        'high': '🟢',
        'medium': '🟡',
        'low': '🔴'
    }.get(confidence.lower(), '⚪')
    
    lines.append(f"📊 <b>Прогноз:</b> {proj.get('prediction', 'Нет данных')}")
    lines.append(f"🎯 <b>Вероятность:</b> {prob:.1%}")
    lines.append(f"💰 <b>Маржа (Edge):</b> {edge:.1%}")
    lines.append(f"📈 <b>EV (Ожидаемая ценность):</b> {ev:.2f}")
    lines.append(f"💵 <b>Келли-ставка:</b> {kelly:.2f} юнитов")
    lines.append(f"📊 <b>Уверенность:</b> {conf_emoji} {confidence}")
    
    # Ключевые факторы
    factors = proj.get('key_factors', [])
    if factors:
        lines.append("📌 <b>Ключевые факторы:</b>")
        for factor in factors[:3]:
            lines.append(f"   • {factor}")
    
    # Топ-риски
    risks = proj.get('top_risks', [])
    if risks:
        lines.append("⚠️ <b>Топ-риски:</b>")
        for risk in risks[:2]:
            lines.append(f"   • {risk}")
    
    return "\n".join(lines)

def main():
    print("🔍 Получение прогнозов с Olympus Bets Analytics...")
    data = get_olympus_projections()
    
    if 'error' in data:
        send_telegram_message(f"❌ Ошибка получения прогнозов:\n{data['error']}")
        return
    
    projections = data.get('projections', {})
    if not projections:
        send_telegram_message("📭 На сегодня прогнозов нет.")
        return
    
    all_messages = []
    header = (
        "🏛️ <b>OLYMPUS BETS ANALYTICS</b>\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y')}\n"
        "⚡ Прогнозы на сегодня\n"
        "=" * 30 + "\n"
    )
    all_messages.append(header)
    
    for sport, projs in projections.items():
        if not projs:
            continue
        
        sport_name = {
            'nba': 'NBA 🏀',
            'nhl': 'NHL 🏒',
            'nfl': 'NFL 🏈',
            'mlb': 'MLB ⚾',
            'cbb': 'CBB 🏀',
            'soccer': 'Футбол ⚽',
            'lol': 'LoL 🎮',
            'golf': 'Гольф ⛳',
            'tennis': 'Теннис 🎾',
            'olympic_hockey': 'Олимпийский хоккей 🏒'
        }.get(sport, sport.upper())
        
        all_messages.append(f"\n🏆 {sport_name}\n" + "-" * 20)
        
        for proj in projs:
            formatted = format_projection(proj, "")
            all_messages.append(formatted)
            all_messages.append("")
    
    # Отправляем историю результатов
    track = get_olympus_track_record()
    if track and 'Ошибка' not in track:
        all_messages.append("\n📊 <b>ИСТОРИЯ РЕЗУЛЬТАТОВ</b>")
        all_messages.append("=" * 30)
        # Показываем последние строки
        lines = track.strip().split('\n')
        if len(lines) > 10:
            all_messages.extend(lines[-10:])
        else:
            all_messages.extend(lines)
    
    # Отправляем все сообщения
    full_text = "\n".join(all_messages)
    for part in split_message(full_text):
        send_telegram_message(part)
    
    print("✅ Прогнозы отправлены в Telegram")

if __name__ == "__main__":
    main()

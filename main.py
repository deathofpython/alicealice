from flask import Flask, request
import logging
import random
import json
import os

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    'Москва': ['213044/aab06daf0747133b7c43', '1030494/55c354c7d62ca8052fc1'],
    'Париж': ['965417/18f8c98f305f8e79f010', '965417/114b329b9690d80ba1fc'],
    'Нью-Йорк': ["1540737/35f34e0c0ff4227f4d3b", '997614/cc126668ce5987b72b4e']
}

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет, меня зовут Алиса! Назови свое имя, смертный!'
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Пока не скажешь имя ничего не узнаешь!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            sessionStorage[user_id]['guessed_cities'] = []
            res['response']['text'] = f'Приветствую тебя, смертный {first_name.title()}! Отгадаешь загадки - получишь много чести!'
            res['response']['buttons'] = [
                {
                    'title': 'Начать игру',
                    'hide': True
                },
                {
                    'title': 'Отказаться',
                    'hide': True
                }
            ]
    else:
        if not sessionStorage[user_id]['game_started']:
            if req['request']['original_utterance'].lower() == 'начать игру':
                if len(sessionStorage[user_id]['guessed_cities']) == 3:
                    res['response']['text'] = 'Ты выполнил все задания, смертный! Не жди от меня вознаграждения!'
                    res['end_session'] = True
                else:
                    sessionStorage[user_id]['game_started'] = True
                    sessionStorage[user_id]['attempt'] = 1
                    play_game(res, req)
            elif req['request']['original_utterance'].lower() == 'отказаться':
                res['response']['text'] = 'До встречи смертный!'
                res['end_session'] = True
            else:
                res['response']['text'] = 'Ты хочешь меня довести, да? Делай, как тебе велят, смертный!'
                res['response']['buttons'] = [
                    {
                        'title': 'Начать игру',
                        'hide': True
                    },
                    {
                        'title': 'Отказаться',
                        'hide': True
                    }
                ]
        else:
            play_game(res, req)


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']
    if attempt == 1:
        city = random.choice(list(cities))
        while city in sessionStorage[user_id]['guessed_cities']:
            city = random.choice(list(cities))
        sessionStorage[user_id]['city'] = city
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Назови город, смертный!'
        res['response']['card']['image_id'] = cities[city][attempt - 1]
        res['response']['text'] = 'РўРѕРіРґР° СЃС‹РіСЂР°РµРј!'
    else:
        city = sessionStorage[user_id]['city']
        if get_city(req) == city:
            res['response']['text'] = 'РџСЂР°РІРёР»СЊРЅРѕ! РЎС‹РіСЂР°РµРј РµС‰С‘?'
            sessionStorage[user_id]['guessed_cities'].append(city)
            sessionStorage[user_id]['game_started'] = False
            return
        else:
            if attempt == 3:
                res['response']['text'] = f'Р’С‹ РїС‹С‚Р°Р»РёСЃСЊ. Р­С‚Рѕ {city.title()}. РЎС‹РіСЂР°РµРј РµС‰С‘?'
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guessed_cities'].append(city)
                return
            else:
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'РќРµРїСЂР°РІРёР»СЊРЅРѕ. Р’РѕС‚ С‚РµР±Рµ РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕРµ С„РѕС‚Рѕ'
                res['response']['card']['image_id'] = cities[city][attempt - 1]
                res['response']['text'] = 'Рђ РІРѕС‚ Рё РЅРµ СѓРіР°РґР°Р»!'
    sessionStorage[user_id]['attempt'] += 1


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    app.run()

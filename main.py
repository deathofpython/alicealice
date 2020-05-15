from flask import Flask, request
import logging
import random
import json
import os

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    ('москва', 'россия'): ['213044/aab06daf0747133b7c43', '1030494/55c354c7d62ca8052fc1'],
    ('париж', 'франция'): ['965417/18f8c98f305f8e79f010', '965417/114b329b9690d80ba1fc'],
    ('нью-йорк', 'америка'): ["1540737/35f34e0c0ff4227f4d3b", '997614/cc126668ce5987b72b4e']
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


def handle_dialog(res, req, *city):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет, меня зовут Алиса! Назови свое имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Пока не скажешь имя, ничего не узнаешь!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            sessionStorage[user_id]['guessed_cities'] = []
            res['response']['text'] = f'Приветствую тебя, {first_name.title()}! Сыграем в игру \'Угадай город\'?'
            res['response']['buttons'] = [
                {
                    'title': 'Играть',
                    'hide': True
                },
                {
                    'title': 'Отказаться',
                    'hide': True
                }
            ]
    else:
        first_name = sessionStorage[user_id]['first_name']
        if not sessionStorage[user_id]['game_started']:
            if req['request']['original_utterance'].lower() == 'играть':
                if len(sessionStorage[user_id]['guessed_cities']) == 3:
                    res['response']['text'] = f'Ты отгадал все города, {first_name.title()}!'
                    res['end_session'] = True
                else:
                    sessionStorage[user_id]['game_started'] = True
                    sessionStorage[user_id]['attempt'] = 1
                    play_game(res, req, user_id)
            elif req['request']['original_utterance'].lower() == 'отказаться':
                res['response']['text'] = f'До встречи, {first_name.title()}!'
                res['end_session'] = True
            elif city:
                if req['request']['original_utterance'].lower() == city[0][1]:
                    res['response']['text'] = f'Правильно! Сыграем еще, {first_name.title()}?'
                else:
                    res['response'][
                        'text'] = f'Город {city[0][0][0].upper() + city[0][0][1:]} находится в стране {city[0][1][0].upper() + city[0][1][1:]}. Сыграем еще, {first_name.title()}?'
            else:
                res['response']['text'] = f'Какую команду ты хочешь мне дать, {first_name.title()}?'
                res['response']['buttons'] = [
                    {
                        'title': 'Играть',
                        'hide': True
                    },
                    {
                        'title': 'Отказаться',
                        'hide': True
                    }
                ]
        else:
            play_game(res, req, user_id)


def play_game(res, req, id):
    first_name = sessionStorage[id]['first_name']
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']
    if attempt == 1:
        city = random.choice(list(cities))
        while city in sessionStorage[user_id]['guessed_cities']:
            city = random.choice(list(cities))
        sessionStorage[user_id]['city'] = city
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = f'Назови город, {first_name.title()}!'
        res['response']['card']['image_id'] = cities[city][attempt - 1]
        res['response']['text'] = ''
    else:
        city = sessionStorage[user_id]['city']
        if get_geo(req) == city[0]:
            res['response']['text'] = f'Правильно! А в какой стране {city[0]}?'
            handle_dialog(res, req, city)
            sessionStorage[user_id]['guessed_cities'].append(city)
            res['response']['buttons'] = [
                {
                    'title': 'Играть',
                    'hide': True
                },
                {
                    'title': 'Отказаться',
                    'hide': True
                },
                {
                    'title': 'Покажи город на карте',
                    'url': f'https://yandex.ru/maps/?mode=search&text={city[0]}',
                    'hide': True
                }
            ]
            sessionStorage[user_id]['game_started'] = False
            return
        else:
            if attempt == 3:
                res['response']['text'] = f'Это - {city[0].title()}. Сыграем еще, {first_name.title()}?'
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guessed_cities'].append(city)
                return
            else:
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = f'Попробуй отгадать тот же город по другой фотографии, {first_name.title()}'
                res['response']['card']['image_id'] = cities[city][attempt - 1]
                res['response']['text'] = ''
    sessionStorage[user_id]['attempt'] += 1


def get_geo(req):
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

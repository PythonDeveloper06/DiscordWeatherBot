import pytest
from config import API_KEY
from mixins import api_weather


@pytest.mark.asyncio
async def test_correct_url():
    city = 'Omsk'
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={API_KEY}'
    assert await api_weather(url) != {'cod': '404', 'message': 'city not found'}


@pytest.mark.asyncio
async def test_incorrect_url():
    city = 'yiguiwqreygyguwuirhfjgkbvjkqriutyghjksfjkhjksg'
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={API_KEY}'
    assert await api_weather(url) == {'cod': '404', 'message': 'city not found'}

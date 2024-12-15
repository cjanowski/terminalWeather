import unittest
from unittest.mock import patch, Mock
from datetime import datetime
from weather import get_weather
import requests

class TestWeather(unittest.TestCase):
    @patch('weather.requests.get')
    def test_get_weather_success(self, mock_get):
        # Mock the responses for both API calls
        mock_location_response = Mock()
        mock_location_response.json.return_value = [{
            'lat': '40.7128',
            'lon': '-74.0060',
            'display_name': 'New York, NY, USA'
        }]
        
        mock_weather_response = Mock()
        mock_weather_response.json.return_value = {
            'current': {
                'temperature_2m': 72,
                'relative_humidity_2m': 65,
                'wind_speed_10m': 10,
                'weather_code': 0
            },
            'daily': {
                'time': ['2024-12-15', '2024-12-16', '2024-12-17', '2024-12-18', '2024-12-19'],
                'temperature_2m_max': [75, 76, 77, 78, 79],
                'temperature_2m_min': [65, 66, 67, 68, 69],
                'weather_code': [0, 1, 2, 3, 0],
                'precipitation_probability_max': [10, 20, 30, 40, 50]
            },
            'hourly': {
                'time': [f'2024-12-15T{h:02d}:00' for h in range(24)],
                'temperature_2m': [70] * 24,
                'precipitation_probability': [10] * 24,
                'weather_code': [0] * 24
            }
        }

        # Configure the mock to return different responses for different URLs
        def mock_get_side_effect(url, **kwargs):
            if 'nominatim.openstreetmap.org' in url:
                return mock_location_response
            elif 'api.open-meteo.com' in url:
                return mock_weather_response
            return Mock()

        mock_get.side_effect = mock_get_side_effect
        mock_location_response.raise_for_status = Mock()
        mock_weather_response.raise_for_status = Mock()

        # Test the function
        result = get_weather('10001')
        
        # Verify the result contains expected data
        self.assertIn('New York', result)
        self.assertIn('72°F', result)
        self.assertIn('65%', result)
        self.assertIn('10 mph', result)
        self.assertIn('Clear sky', result)

    @patch('weather.requests.get')
    def test_get_weather_invalid_zip(self, mock_get):
        # Mock empty response for invalid ZIP code
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_weather('00000')
        self.assertEqual(result, 'Error: ZIP code not found')

    @patch('weather.requests.get')
    def test_get_weather_api_error(self, mock_get):
        # Mock API error
        mock_get.side_effect = requests.exceptions.RequestException('API Error')
        
        result = get_weather('10001')
        self.assertIn('Error fetching weather data', result)

if __name__ == '__main__':
    unittest.main()

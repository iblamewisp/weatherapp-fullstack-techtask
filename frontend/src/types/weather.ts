export interface WeatherResponse {
  id: string;
  city: string;
  country: string;
  latitude: number | null;
  longitude: number | null;
  temperature: number | null;
  feels_like: number | null;
  humidity: number | null;
  pressure: number | null;
  wind_speed: number | null;
  weather_description: string | null;
  weather_icon: string | null;
  last_updated: string;
  created_at: string;
}

import { z } from "zod";

export const cityFormSchema = z.object({
  mode: z.literal("city"),
  city: z.string().min(1, "City is required").max(100),
  country: z
    .string()
    .length(2, "Country must be exactly 2 characters")
    .regex(/^[a-zA-Z]+$/, "Country must contain only letters"),
});

export const coordsFormSchema = z.object({
  mode: z.literal("coords"),
  latitude: z.coerce
    .number()
    .min(-90, "Latitude must be >= -90")
    .max(90, "Latitude must be <= 90"),
  longitude: z.coerce
    .number()
    .min(-180, "Longitude must be >= -180")
    .max(180, "Longitude must be <= 180"),
});

export const weatherFormSchema = z.discriminatedUnion("mode", [
  cityFormSchema,
  coordsFormSchema,
]);

export type WeatherFormValues = z.infer<typeof weatherFormSchema>;
export type CityFormValues = z.infer<typeof cityFormSchema>;
export type CoordsFormValues = z.infer<typeof coordsFormSchema>;

// Only exposes fields that make sense for a user to manually override.
// City/country/coordinates are intentionally excluded.
export const createWeatherSchema = z.object({
  city: z.string().min(1, "City is required").max(100),
  country: z
    .string()
    .length(2, "Must be exactly 2 characters")
    .regex(/^[a-zA-Z]+$/, "Letters only"),
  latitude: z.coerce.number().min(-90).max(90).optional().nullable(),
  longitude: z.coerce.number().min(-180).max(180).optional().nullable(),
  temperature: z.coerce.number().min(-100).max(60).optional().nullable(),
  feels_like: z.coerce.number().min(-100).max(60).optional().nullable(),
  humidity: z.coerce.number().int().min(0).max(100).optional().nullable(),
  pressure: z.coerce.number().int().min(870).max(1084).optional().nullable(),
  wind_speed: z.coerce.number().min(0).max(500).optional().nullable(),
  weather_description: z.string().max(100).optional().nullable(),
});

export type CreateWeatherValues = z.infer<typeof createWeatherSchema>;

export const editWeatherSchema = z.object({
  temperature: z.coerce.number().min(-100).max(60).nullable().optional(),
  feels_like: z.coerce.number().min(-100).max(60).nullable().optional(),
  humidity: z.coerce.number().int().min(0).max(100).nullable().optional(),
  pressure: z.coerce.number().int().min(870).max(1084).nullable().optional(),
  wind_speed: z.coerce.number().min(0).max(500).nullable().optional(),
  weather_description: z.string().max(100).nullable().optional(),
});

export type EditWeatherValues = z.infer<typeof editWeatherSchema>;

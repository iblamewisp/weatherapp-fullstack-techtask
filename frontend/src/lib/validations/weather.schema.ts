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

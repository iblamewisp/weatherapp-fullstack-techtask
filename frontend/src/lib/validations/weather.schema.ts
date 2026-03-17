import { z } from "zod";

export const cityFormSchema = z.object({
  mode: z.literal("city"),
  city: z.string().min(1, "City is required"),
  country: z.string().max(2, "Use 2-letter country code").optional().or(z.literal("")),
});

export const coordsFormSchema = z.object({
  mode: z.literal("coords"),
  latitude: z.coerce.number().min(-90, "Must be between -90 and 90").max(90, "Must be between -90 and 90"),
  longitude: z.coerce.number().min(-180, "Must be between -180 and 180").max(180, "Must be between -180 and 180"),
});

export type CityFormValues = z.infer<typeof cityFormSchema>;
export type CoordsFormValues = z.infer<typeof coordsFormSchema>;

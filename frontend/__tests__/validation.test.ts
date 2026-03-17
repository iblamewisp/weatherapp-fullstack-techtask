import { cityFormSchema, coordsFormSchema } from "../src/lib/validations/weather.schema";

describe("City form validation", () => {
  it("valid city passes", () => {
    const result = cityFormSchema.safeParse({ mode: "city", city: "London", country: "GB" });
    expect(result.success).toBe(true);
  });

  it("single char country fails", () => {
    const result = cityFormSchema.safeParse({ mode: "city", city: "London", country: "G" });
    expect(result.success).toBe(false);
  });

  it("3 char country fails", () => {
    const result = cityFormSchema.safeParse({ mode: "city", city: "London", country: "GBR" });
    expect(result.success).toBe(false);
  });

  it("digits in country fails", () => {
    const result = cityFormSchema.safeParse({ mode: "city", city: "London", country: "G1" });
    expect(result.success).toBe(false);
  });

  it("empty city fails", () => {
    const result = cityFormSchema.safeParse({ mode: "city", city: "", country: "GB" });
    expect(result.success).toBe(false);
  });
});

describe("Coordinates form validation", () => {
  it("valid coords pass", () => {
    const result = coordsFormSchema.safeParse({ mode: "coords", latitude: 51.5, longitude: -0.12 });
    expect(result.success).toBe(true);
  });

  it("latitude > 90 fails", () => {
    const result = coordsFormSchema.safeParse({ mode: "coords", latitude: 91, longitude: 0 });
    expect(result.success).toBe(false);
  });

  it("latitude < -90 fails", () => {
    const result = coordsFormSchema.safeParse({ mode: "coords", latitude: -91, longitude: 0 });
    expect(result.success).toBe(false);
  });

  it("longitude > 180 fails", () => {
    const result = coordsFormSchema.safeParse({ mode: "coords", latitude: 0, longitude: 181 });
    expect(result.success).toBe(false);
  });

  it("longitude < -180 fails", () => {
    const result = coordsFormSchema.safeParse({ mode: "coords", latitude: 0, longitude: -181 });
    expect(result.success).toBe(false);
  });
});

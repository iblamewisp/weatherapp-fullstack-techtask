const nextJest = require("next/jest");
const createJestConfig = nextJest({ dir: "./" });
const customJestConfig = {
  setupFilesAfterFramework: ["@testing-library/jest-dom"],
  testEnvironment: "jsdom",
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
};
module.exports = createJestConfig(customJestConfig);

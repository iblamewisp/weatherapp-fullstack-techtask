import { WeatherForm } from "@/components/WeatherForm";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-md">
        <h1 className="text-4xl font-bold text-center text-gray-800 mb-2">Weather App</h1>
        <p className="text-center text-gray-500 mb-8">Search by city or coordinates</p>
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <WeatherForm />
        </div>
      </div>
    </main>
  );
}

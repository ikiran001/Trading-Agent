"use client";

export function ConfidenceMeter({ value }: { value: number }) {
  const color = value >= 70 ? "bg-accent" : value >= 50 ? "bg-yellow-500" : "bg-danger";
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span>Market confidence</span>
        <span>{Math.round(value)}%</span>
      </div>
      <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} transition-all duration-500`} style={{ width: `${Math.min(100, value)}%` }} />
      </div>
    </div>
  );
}

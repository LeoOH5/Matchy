interface Props {
  steps: string[];
  current: number;
}

export default function StepIndicator({ steps, current }: Props) {
  return (
    <div className="flex items-center justify-center gap-0 mb-8">
      {steps.map((label, i) => (
        <div key={i} className="flex items-center">
          <div className="flex flex-col items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                i < current
                  ? "bg-blue-600 text-white"
                  : i === current
                  ? "bg-blue-600 text-white ring-4 ring-blue-100"
                  : "bg-gray-200 text-gray-400"
              }`}
            >
              {i < current ? (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                i + 1
              )}
            </div>
            <span
              className={`mt-1 text-xs whitespace-nowrap ${
                i === current ? "text-blue-600 font-semibold" : "text-gray-400"
              }`}
            >
              {label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div
              className={`w-12 h-0.5 mx-1 mb-4 transition-colors ${
                i < current ? "bg-blue-600" : "bg-gray-200"
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );
}

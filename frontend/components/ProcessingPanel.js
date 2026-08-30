export default function ProcessingPanel({ processing }) {
  return (
    <section 
      className="flex h-full w-full flex-col items-center justify-center px-4" 
      aria-live="polite"
    >
      <div className="flex flex-col items-center text-center">
        {/* Pulsing Loading Graphic */}
        <div className="relative mb-[24px] h-[100px] w-[100px] sm:h-[120px] sm:w-[120px] animate-pulse">
          <img 
            src="/assets/loading.png" 
            alt="Loading..." 
            className="h-full w-full object-contain"
          />
        </div>

        {/* Text content */}
        <h2 className="text-[28px] sm:text-[34px] font-bold leading-none tracking-[-1.5px] text-[#272727]">
          Extracting...
        </h2>
        <p className="mt-[8px] text-[15px] sm:text-[17px] font-normal leading-[22px] text-[#9CA3AF]">
          This may take a while
        </p>
      </div>
    </section>
  );
}

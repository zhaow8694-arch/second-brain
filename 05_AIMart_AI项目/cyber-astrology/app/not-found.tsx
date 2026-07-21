import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#030712] flex flex-col items-center justify-center p-6 text-center space-y-8">
      <div className="relative">
        <div className="text-8xl md:text-9xl font-black text-cyan-500/20 animate-pulse select-none">
          404
        </div>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-4xl md:text-6xl font-black text-cyan-500 tracking-tighter uppercase italic">
            Signal <span className="text-white">Lost</span>
          </div>
        </div>
      </div>

      <div className="max-w-md space-y-4">
        <p className="text-gray-400 font-mono text-xs uppercase tracking-widest leading-relaxed">
          The dimension you are trying to reach does not exist in this matrix.
          <br />
          <span className="text-gray-600">量子信号已超出矩阵边界。</span>
        </p>
      </div>

      <div className="flex gap-4">
        <Link
          href="/"
          className="px-8 py-3 bg-cyan-500 hover:bg-cyan-400 text-black font-black uppercase text-xs rounded-xl transition-all shadow-[0_0_30px_rgba(6,182,212,0.3)]"
        >
          Return to Hall
        </Link>
      </div>

      <div className="absolute inset-0 pointer-events-none opacity-[0.03] overflow-hidden">
        <div className="h-full w-full bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]"></div>
      </div>
    </div>
  );
}
